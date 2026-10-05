"""invest-agent：指标计算、取数顺序、报告转义、接口的出错路径。AkShare 和 OpenAI 都换成假的，不联网。"""
import json
import os
import sys
import types

import pytest

from helpers import ROOT

pd = pytest.importorskip("pandas")
pytest.importorskip("fastapi")
pytest.importorskip("openai")
pytest.importorskip("httpx")

AGENT = ROOT / "agents/invest-agent"


def fake_daily(n=30, start=10.0):
    closes = [start + i * 0.1 for i in range(n)]
    closes[-1] = closes[-2] - 0.5                         # 最后一天跌一下，好算回撤
    pct = [0.0] + [(closes[i] / closes[i - 1] - 1) * 100 for i in range(1, n)]
    return pd.DataFrame({
        "日期": pd.date_range("2026-08-01", periods=n).strftime("%Y-%m-%d"),
        "开盘": closes, "收盘": closes,
        "最高": [c + 0.2 for c in closes], "最低": [c - 0.2 for c in closes],
        "成交量": [1000 + (200 if p > 0 else 0) for p in pct],
        "成交额": closes, "振幅": [1.0] * n, "涨跌幅": pct, "涨跌额": [0.0] * n, "换手率": [1.5] * n,
    })


@pytest.fixture(scope="module")
def mods():
    """在假的 akshare 上导入 invest-agent 的模块。"""
    ak = types.ModuleType("akshare")
    ak.calls = []

    def hist(**kw):
        ak.calls.append(kw)
        return fake_daily(60).astype(str)               # AkShare 有时返回字符串列，验证会转成数字

    ak.stock_zh_a_hist = ak.fund_etf_hist_em = hist
    # 两个接口真实返回都是按日期从早到晚
    ak.stock_financial_abstract_ths = lambda **kw: pd.DataFrame({"报告期": ["2024-12-31", "2025-06-30", "2025-12-31", "2026-06-30"], "净利润": ["1", "2", "3", "4"]})
    ak.fund_etf_fund_info_em = lambda **kw: pd.DataFrame({"净值日期": ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"], "单位净值": ["1.0", "1.1", "1.2", "1.3"]})

    saved = {k: sys.modules.get(k) for k in ("akshare", "config", "report", "app")}
    sys.modules["akshare"] = ak
    os.environ.setdefault("OPENAI_API_KEY", "test")
    os.environ["AKSHARE_PROXY"] = ""
    sys.path.insert(0, str(AGENT))
    import app, report
    from tools import akshare_client, indicators
    yield types.SimpleNamespace(app=app, report=report, client=akshare_client, ind=indicators, ak=ak)
    sys.path.remove(str(AGENT))
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def test_summarize(mods):
    df = fake_daily(30)
    s = mods.ind.summarize(df)
    assert s["最新收盘"] == round(df["收盘"].iloc[-1], 2)
    assert s["区间涨跌幅%"] == round((df["收盘"].iloc[-1] / 10 - 1) * 100, 2)
    assert s["MA5"] == round(df["收盘"].tail(5).mean(), 2)
    assert s["区间最大回撤%"] < 0
    assert s["上涨日均量/下跌日均量"] == 1.2
    assert 0 <= s["收盘在区间的位置%"] <= 100


def test_summarize_short_history(mods):
    s = mods.ind.summarize(fake_daily(4))               # 新股：不够 5 天就不算均线
    assert "MA5" not in s and "近5日均量/之前均量" not in s


def test_daily_is_numeric_and_trimmed(mods):
    df = mods.client.get_daily("600519")
    assert len(df) == 30
    assert df["收盘"].dtype.kind == "f"
    assert "start_date" in mods.ak.calls[-1]            # 不再拉上市以来的全部日线


def test_financials_take_latest_first(mods):
    df = mods.client.get_financials("600519")
    assert list(df["报告期"]) == ["2026-06-30", "2025-12-31", "2025-06-30"]
    nav = mods.client.get_financials("510300")
    assert list(nav["净值日期"]) == ["2026-10-01", "2026-09-30", "2026-09-29"]


def test_report_escapes_html(mods):
    page = mods.report.render("<b>x</b>", "估值 PE<20 & ROE>15\n```mermaid\ngraph LR\nA<-->B\n```\n</pre><script>alert(1)</script>")
    raw = page.split('<pre id="raw-content" style="display:none">')[1].split("</pre>\n</body>")[0]
    assert "<" not in raw and "PE&lt;20 &amp; ROE&gt;15" in raw
    assert "<b>x</b>" not in page


def test_endpoint(mods, monkeypatch):
    from fastapi.testclient import TestClient
    seen = {}
    monkeypatch.setattr(mods.app, "analyze", lambda d: seen.setdefault("data", d) and "# 分析 PE<20")
    monkeypatch.setattr(mods.app, "risk_analysis", lambda d: "## 六、风险")
    c = TestClient(mods.app.app)

    r = c.get("/analyze/600519.SH")
    assert r.status_code == 200 and "PE&lt;20" in r.text and "六、风险" in r.text
    assert seen["data"]["类型"] == "股票" and "已算好的指标" in seen["data"]
    json.dumps(seen["data"], ensure_ascii=False)          # 提示词里要 json.dumps，不能有 numpy 类型

    assert c.get("/analyze/abc").status_code == 400


def test_endpoint_data_error(mods, monkeypatch):
    from fastapi.testclient import TestClient

    def boom(symbol):
        raise mods.client.DataError("连不上代理")
    monkeypatch.setattr(mods.app, "get_daily", boom)
    r = TestClient(mods.app.app).get("/analyze/600519")
    assert r.status_code == 502 and "连不上代理" in r.text
