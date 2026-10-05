def plan(symbol):
    return {
        "tasks": [
            "fetch_stock_data",
            "fetch_financials",
            "run_analysis",
            "run_risk_check"
        ],
        "symbol": symbol
    }