from dotenv import load_dotenv
load_dotenv()

import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from agent.planner import plan
from agent.analyst import analyze
from agent.risk import risk_analysis
from tools.tushare_client import get_daily, get_financials

app = FastAPI()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{symbol} · 投资分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: false, theme: 'default' }});

  window.addEventListener('DOMContentLoaded', async () => {{
    const raw = document.getElementById('raw-content').textContent;
    document.getElementById('report').innerHTML = marked.parse(raw);

    document.querySelectorAll('code.language-mermaid').forEach(el => {{
      const div = document.createElement('div');
      div.className = 'mermaid';
      div.textContent = el.textContent;
      el.parentElement.replaceWith(div);
    }});

    await mermaid.run();
  }});
</script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f6fa;
    color: #2c3e50;
    line-height: 1.7;
  }}
  header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    padding: 32px 40px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  header h1 {{ font-size: 1.8rem; font-weight: 700; letter-spacing: 1px; }}
  header p {{ opacity: 0.7; font-size: 0.9rem; margin-top: 4px; }}
  #report {{
    max-width: 960px;
    margin: 40px auto;
    padding: 0 20px 60px;
  }}
  #report h1 {{
    font-size: 1.6rem;
    color: #1a1a2e;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 12px;
    margin: 40px 0 20px;
  }}
  #report h2 {{
    font-size: 1.2rem;
    color: #0f3460;
    margin: 32px 0 14px;
    padding-left: 12px;
    border-left: 4px solid #e94560;
  }}
  #report h3 {{
    font-size: 1rem;
    color: #2c3e50;
    margin: 20px 0 10px;
  }}
  #report p {{ margin: 10px 0; }}
  #report table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  #report th {{
    background: #1a1a2e;
    color: white;
    padding: 12px 16px;
    text-align: left;
    font-size: 0.85rem;
    font-weight: 600;
  }}
  #report td {{
    padding: 11px 16px;
    border-bottom: 1px solid #eef0f4;
    font-size: 0.9rem;
  }}
  #report tr:last-child td {{ border-bottom: none; }}
  #report tr:hover td {{ background: #f8f9ff; }}
  #report blockquote {{
    background: #fff8e1;
    border-left: 4px solid #ffc107;
    padding: 12px 16px;
    margin: 20px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
    color: #7a6000;
  }}
  #report strong {{ color: #0f3460; }}
  #report .mermaid {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    text-align: center;
  }}
  #report hr {{
    border: none;
    border-top: 1px solid #e0e3ec;
    margin: 32px 0;
  }}
</style>
</head>
<body>
<header>
  <h1>📈 {symbol} · 投资分析报告</h1>
  <p>基于近30个交易日数据 · AI 生成 · 仅供研究参考</p>
</header>
<div id="report"></div>
<pre id="raw-content" style="display:none">{content}</pre>
</body>
</html>"""

@app.get("/analyze/{ts_code}", response_class=HTMLResponse)
def analyze_stock(ts_code: str):
    plan(ts_code)

    price = get_daily(ts_code)
    finance = get_financials(ts_code)

    data = {
        "price_data": price.to_dict("records"),
        "finance_data": finance.head(3).to_dict("records")
    }

    analysis = analyze(data)
    risk = risk_analysis(data)

    content = analysis + "\n\n---\n\n" + risk
    content_escaped = content.replace("`", "&#96;").replace("${", "&#36;{")

    return HTML_TEMPLATE.format(symbol=ts_code, content=content_escaped)
