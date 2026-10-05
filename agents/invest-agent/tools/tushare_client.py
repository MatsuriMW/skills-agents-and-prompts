import os
import requests
import akshare as ak

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

_PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

_orig_get = requests.get
def _get_via_clash(url, **kwargs):
    kwargs["proxies"] = _PROXY
    return _orig_get(url, **kwargs)
requests.get = _get_via_clash

def _is_etf(symbol):
    return symbol.startswith(("51", "15", "16", "18", "56", "58"))

def get_daily(ts_code):
    symbol = ts_code.split(".")[0]
    if _is_etf(symbol):
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq").tail(30)
    else:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(30)
    return df.astype(str)

def get_financials(ts_code):
    symbol = ts_code.split(".")[0]
    if _is_etf(symbol):
        df = ak.fund_etf_fund_info_em(fund=symbol)
        return df.astype(str)
    else:
        df = ak.stock_financial_abstract_ths(symbol=symbol)
        return df.astype(str)
