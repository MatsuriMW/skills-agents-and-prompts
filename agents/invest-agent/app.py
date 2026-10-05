import re
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from agent.analyst import analyze
from agent.risk import risk_analysis
from report import render, render_error
from tools.akshare_client import DataError, get_daily, get_financials, is_etf
from tools.indicators import recent_rows, summarize

app = FastAPI()

CODE = re.compile(r"^(\d{6})(?:\.(?:SH|SZ|BJ))?$", re.I)


@app.get("/analyze/{ts_code}", response_class=HTMLResponse)
def analyze_stock(ts_code: str):
    m = CODE.match(ts_code.strip())
    if not m:
        return HTMLResponse(render_error(ts_code, "代码格式不对：要 6 位数字，可以带 .SH / .SZ / .BJ，例如 600519.SH、510300"), status_code=400)
    symbol = m.group(1)

    try:
        price = get_daily(symbol)
        finance = get_financials(symbol)
    except DataError as e:
        return HTMLResponse(render_error(ts_code, str(e)), status_code=502)

    etf = is_etf(symbol)
    data = {
        "代码": ts_code,
        "类型": "ETF" if etf else "股票",
        "已算好的指标": summarize(price),
        "最近10个交易日": recent_rows(price),
        ("最近几天的基金净值" if etf else "最近3个报告期的财务摘要（从新到旧）"): finance.to_dict("records"),
    }

    # 两次模型调用互不依赖，并行跑
    with ThreadPoolExecutor(max_workers=2) as pool:
        analysis, risk = pool.submit(analyze, data), pool.submit(risk_analysis, data)
        try:
            content = analysis.result() + "\n\n---\n\n" + risk.result()
        except Exception as e:
            return HTMLResponse(render_error(ts_code, f"调用模型失败（{type(e).__name__}: {e}）"), status_code=502)

    return render(ts_code, content)
