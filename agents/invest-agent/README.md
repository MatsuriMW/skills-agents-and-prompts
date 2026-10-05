# invest-agent：A 股 / ETF 分析报告

输入一个股票或 ETF 代码，拉最近 30 个交易日行情和财务摘要，让 GPT 写一份带表格和 Mermaid 图的中文分析报告，在浏览器里看。2026-04 写的练手项目，本机在 `~/Documents/agents/自己写的/invest-agent`。

## 流程

`app.py` 里的 `GET /analyze/{代码}`：

1. 校验代码（6 位数字，可带 `.SH` / `.SZ` / `.BJ`），不对直接报错
2. `tools/akshare_client.py`：用 **AkShare**（免费，不要 token）取最近 30 个交易日的前复权日线，股票再取最近 3 个报告期的财务摘要（从新到旧），ETF 取最近几天的净值。代码以 51/15/16/18/56/58 开头的当 ETF 处理。请求默认走本机 Clash 代理 `127.0.0.1:7897`，可以在 `.env` 里用 `AKSHARE_PROXY` 改或关掉；连不上代理会直接说
3. `tools/indicators.py`：均线、区间涨跌、最大回撤、波动率、量价比这些数字**在程序里算好**，模型只负责解读，不让它从原始行情里心算
4. `agent/analyst.py`（价格 + 财务分析）和 `agent/risk.py`（估值 / 政策 / 流动性 / 盈利四类风险）**并行**调用模型，都是 few-shot + 分步思考的提示词。数据里没有 PE、行业均值、政策，提示词要求这些写「数据未提供」或标「推断」，不许编数字。模型默认 `gpt-4o-mini`，`.env` 里 `OPENAI_MODEL` 可换
5. `report.py`：报告转义后套进网页，浏览器里用 marked + mermaid 渲染。取数或模型出错时也返回一页说明，不是 500

## 运行

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填上 OPENAI_API_KEY
venv/bin/uvicorn app:app --reload
# 打开 http://127.0.0.1:8000/analyze/600519.SH
```

测试在仓库根目录：`python3 -m pytest tests/test_invest_agent.py`（AkShare 和 OpenAI 都用假的，不联网）。

## 没放进来的

本机目录里的 `.claude/skills/` 有 7 个 skill（question-refiner、research-executor、stock-question-refiner、stock-research-executor、got-controller、citation-validator、synthesizer），是从下载的 `Claude-Code-Stock-Deep-Research-Agent` 原样复制的，是别人的，没传。那个下载的仓库 2026-10-06 已删，里面唯一有用的提示词抽到了 [股票研究八步提示词](../../prompts/股票研究八步提示词.md)。

本机的虚拟环境（1G）2026-10-06 已删，要跑的话按上面重新装。
