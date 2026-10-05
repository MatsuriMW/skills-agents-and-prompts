"""从日线算出报告要用的指标。数字在这里算好再交给模型，不让模型自己从原始行情里心算。"""
import math


def _r(x, nd=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def summarize(df):
    """df：按日期从早到晚的日线，列名同 AkShare（日期 / 收盘 / 最高 / 最低 / 涨跌幅 / 成交量 / 换手率）。"""
    close = df["收盘"]
    n = len(df)
    last = close.iloc[-1]
    out = {
        "区间": f"{df['日期'].iloc[0]} 至 {df['日期'].iloc[-1]}（{n} 个交易日）",
        "最新收盘": _r(last),
        "区间涨跌幅%": _r((last / close.iloc[0] - 1) * 100),
    }
    for w in (5, 10, 20):
        if n >= w:
            ma = close.tail(w).mean()
            out[f"MA{w}"] = _r(ma)
            out[f"收盘相对MA{w}%"] = _r((last / ma - 1) * 100)

    hi, lo = df["最高"].max(), df["最低"].min()
    out["区间最高"], out["区间最低"] = _r(hi), _r(lo)
    out["收盘在区间的位置%"] = _r((last - lo) / (hi - lo) * 100) if hi > lo else None
    out["区间最大回撤%"] = _r(((close / close.cummax()) - 1).min() * 100)

    pct = df["涨跌幅"].dropna()
    if len(pct) > 1:
        out["日涨跌幅标准差%"] = _r(pct.std())
        out["年化波动率%"] = _r(pct.std() * math.sqrt(252))
    out["上涨天数"], out["下跌天数"] = int((pct > 0).sum()), int((pct < 0).sum())

    if "换手率" in df:
        out["平均换手率%"] = _r(df["换手率"].mean())
    vol = df["成交量"]
    up, down = vol[df["涨跌幅"] > 0].mean(), vol[df["涨跌幅"] < 0].mean()
    if up == up and down == down and down > 0:          # 两边都有数据（NaN != NaN）
        out["上涨日均量/下跌日均量"] = _r(up / down)
    if n >= 10:
        out["近5日均量/之前均量"] = _r(vol.tail(5).mean() / vol.iloc[:-5].mean())
    return out


def recent_rows(df, k=10):
    """给模型画表和图用的最近 k 天，只留几列。"""
    cols = [c for c in ("日期", "收盘", "涨跌幅", "成交量", "换手率") if c in df.columns]
    return df[cols].tail(k).to_dict("records")
