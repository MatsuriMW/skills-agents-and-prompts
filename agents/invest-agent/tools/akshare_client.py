from datetime import date, timedelta

import akshare as ak
import pandas as pd
import requests

from config import AKSHARE_PROXY

# AkShare 内部直接调 requests.get，没有传代理的口子，只能在这里包一层。
# 只在调用方没指定 proxies 时补上，不改环境变量，不影响 OpenAI 等别的库。
if AKSHARE_PROXY:
    _orig_get = requests.get

    def _get_via_proxy(url, **kwargs):
        kwargs.setdefault("proxies", {"http": AKSHARE_PROXY, "https": AKSHARE_PROXY})
        return _orig_get(url, **kwargs)

    requests.get = _get_via_proxy


class DataError(Exception):
    """取数失败，消息直接给用户看。"""


PRICE_COLS = ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]


def is_etf(symbol):
    return symbol.startswith(("51", "15", "16", "18", "56", "58"))


def _fetch(fn, **kwargs):
    try:
        return fn(**kwargs)
    except requests.exceptions.ProxyError as e:
        raise DataError(f"连不上代理 {AKSHARE_PROXY}：Clash 开着吗？不用代理就在 .env 里写 AKSHARE_PROXY=") from e
    except Exception as e:
        raise DataError(f"AkShare 取数失败（{type(e).__name__}: {e}）") from e


def get_daily(symbol, days=30):
    """最近 days 个交易日的前复权日线，数值列转成数字，按日期从早到晚。"""
    # 不传 start_date 会把上市以来的全部日线拉下来，这里只取最近两个多月
    start = (date.today() - timedelta(days=days * 2 + 30)).strftime("%Y%m%d")
    fn = ak.fund_etf_hist_em if is_etf(symbol) else ak.stock_zh_a_hist
    df = _fetch(fn, symbol=symbol, period="daily", start_date=start, adjust="qfq")
    if df is None or df.empty:
        raise DataError(f"{symbol} 没有行情数据，代码对吗？")
    df = df.tail(days).reset_index(drop=True)
    for c in PRICE_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["日期"] = df["日期"].astype(str)
    return df


def get_financials(symbol, n=3):
    """股票：最近 n 个报告期的财务摘要，从新到旧。ETF 没有财务报表，返回最近 n 天的净值。"""
    if is_etf(symbol):
        start = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        df = _fetch(ak.fund_etf_fund_info_em, fund=symbol, start_date=start)
    else:
        df = _fetch(ak.stock_financial_abstract_ths, symbol=symbol)
    # AkShare 两个接口都按日期从早到晚排，要最近的得从尾巴取
    return df.tail(n).iloc[::-1].astype(str).reset_index(drop=True)
