# openai-rag：OpenAI File Search 小脚本

2026-04 写的练手脚本，本机在 `~/Documents/agents/自己写的/openai-rag`。把 Markdown 和 PDF 传到 OpenAI 的向量库（vector store），然后用 Responses API 的 File Search 对它们提问，模型是 `gpt-4o-mini`。

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填上 OPENAI_API_KEY
.venv/bin/python rag.py upload 文件或目录…
.venv/bin/python rag.py query "问题"
.venv/bin/python rag.py status    # 看向量库里有哪些文件
.venv/bin/python rag.py reset     # 删掉向量库，从头来
```

向量库的 ID 记在本地的 `.rag_state.json`（没进仓库）。

**现状：价值不大了。** 查自己的笔记现在用 [vault-ask](../../skills/vault-ask) 和 koubo-writer 的语义检索，都在本机跑，不用把笔记传到 OpenAI。留着只当一个 RAG 的最小示例。
