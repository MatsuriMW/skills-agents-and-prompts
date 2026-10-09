# invest-agent：A 股 / ETF 分析报告

输入一个 A 股或 ETF 代码，自动拉最近 30 个交易日的行情和财务摘要，让 GPT 分别做走势分析、财务分析和风险评级，最后生成一份带表格和 Mermaid 图的中文网页报告。

适合用来理解「一个分步骤的 LLM 分析 agent」是怎么搭起来的：规划 → 取数 → 分析 → 风险评估 → 汇总，每一步一个文件，提示词都是 few-shot + 分步思考。**报告只是练习，不构成投资建议。**

## 流程

`app.py` 里的 `GET /analyze/{代码}` 依次调用：

1. `agent/planner.py`：列出要做的四步（目前是固定清单）
2. `tools/tushare_client.py`：取数据。文件名沿用了 tushare，实际用的是 **AkShare**（免费，不需要 token）。代码以 51 / 15 / 16 / 18 / 56 / 58 开头的当 ETF 处理
3. `agent/analyst.py`：价格 + 财务分析，模型 `gpt-4o-mini`
4. `agent/risk.py`：估值 / 政策 / 流动性 / 盈利四类风险评级
5. `agent/synthesizer.py`：拼成报告并加免责声明，`app.py` 用 marked + mermaid 渲染成网页

## 运行

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
echo 'OPENAI_API_KEY=...' > .env
venv/bin/uvicorn app:app --reload
# 打开 http://127.0.0.1:8000/analyze/600519.SH
```

`tools/tushare_client.py` 里的请求默认走本地代理 `127.0.0.1:7897`（`_PROXY`），你不需要代理的话把它和用到它的那一行删掉。

想做更深入的公司研究，可以配合 [股票研究八步提示词](../../prompts/股票研究八步提示词.md)。
