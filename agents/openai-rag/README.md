# openai-rag：OpenAI File Search 最小示例

一个两百来行的 RAG 脚本：把 Markdown 和 PDF 传到 OpenAI 的向量库（vector store），再用 Responses API 的 File Search 对它们提问，模型是 `gpt-4o-mini`。适合想快速看懂「上传 → 检索 → 回答」这条链路的人。

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
echo 'OPENAI_API_KEY=...' > .env
.venv/bin/python rag.py upload 文件或目录…
.venv/bin/python rag.py query "问题"
.venv/bin/python rag.py status    # 看向量库里有哪些文件
.venv/bin/python rag.py reset     # 删掉向量库，从头来
```

向量库的 ID 记在本地的 `.rag_state.json`。

如果你的笔记不想传到云端，可以看本机跑的方案：[vault-ask](../../skills/vault-ask) 和 [第二大脑](https://github.com/MatsuriMW/Obsidian-Plugins/tree/main/second-brain)（本地向量模型 + BM25）。
