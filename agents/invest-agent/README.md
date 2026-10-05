# invest-agent：A 股 / ETF 分析报告

输入一个股票或 ETF 代码，拉最近 30 个交易日行情和财务摘要，让 GPT 写一份带表格和 Mermaid 图的中文分析报告，在浏览器里看。2026-04 写的练手项目。

## 流程

`app.py` 里的 `GET /analyze/{代码}` 依次调用：

1. `agent/planner.py`：列出要做的四步（目前是写死的清单）
2. `tools/tushare_client.py`：取数据。文件名叫 tushare，实际用的是 **AkShare**（免费，不要 token），请求强制走本机 Clash 代理 `127.0.0.1:7897`。代码以 51/15/16/18/56/58 开头的当 ETF 处理
3. `agent/analyst.py`：价格 + 财务分析，few-shot + 分步思考的提示词，模型 `gpt-4o-mini`
4. `agent/risk.py`：估值 / 政策 / 流动性 / 盈利四类风险评级，同样是 few-shot 提示词
5. `agent/synthesizer.py`：拼起来加免责声明，`app.py` 用 marked + mermaid 渲染成网页

## 运行

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt akshare
echo 'OPENAI_API_KEY=...' > .env
venv/bin/uvicorn app:app --reload
# 打开 http://127.0.0.1:8000/analyze/600519.SH
```

`requirements.txt` 里漏了 `akshare`，上面命令里补上了。`.env` 里原来还有个 `TUSHARE_TOKEN`，现在的代码用不到。

## 没放进来的

本机目录 `~/Documents/agents/invest-agent/.claude/skills/` 里有 7 个 skill（question-refiner、research-executor、stock-question-refiner、stock-research-executor、got-controller、citation-validator、synthesizer），和下载的 `Claude-Code-Stock-Deep-Research-Agent` 一模一样，是别人的，没传。
