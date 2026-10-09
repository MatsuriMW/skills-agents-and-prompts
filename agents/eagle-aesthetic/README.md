# eagle-aesthetic：按「感觉」在 Eagle 里找图（未完成）

设计师的素材库越攒越大，按文件夹和标签已经很难找到「那种感觉」的图。这个项目参照 @Sutao_1324 的文章「Eagle × SigLIP2 × Agent」，给 [Eagle](https://eagle.cool) 素材库建一个向量索引：用一句话（「大面积留白、只有一行小字的海报」）或一张参考图，就能找出气质相近的图，并给还没分类的图推荐风格。

- 模型：`google/siglip2-so400m-patch14-384`，图和文字映射到同一个向量空间，所以可以用一句话找图
- **对 Eagle 只读**：通过 Eagle 本地 API（`localhost:41595`）读取，不打标签、不移动文件
- 我自己的库里跑了约 8,400 张海报排版图

## 脚本

| 文件 | 干嘛的 |
|---|---|
| `common.py` | Eagle 本地 API、模型加载、索引读写的公共函数 |
| `download_model.py` | 从 Hugging Face 分块并行下载模型到 `models/`，能断点续传 |
| `build_index.py` | 给「海报排版」里的图算向量，存到 `index/`；增量，已经算过的跳过 |
| `search.py` | 找图：一句话描述、一张参考图，或者「和某张图像的」；`--sheet` 出缩略图拼版，`--open N` 在 Eagle 里打开，`--json` 给 Agent 调用 |
| `classify.py` | 用已经分好风格的图当样本，给没分类的图推荐风格。只出清单（`reports/classify.csv`），不写回 Eagle |

```bash
.venv/bin/python search.py "大面积留白、只有一行小字的海报" --sheet
```

依赖：torch、transformers、numpy、Pillow、scikit-learn。模型约 4.3G，第一次用先跑 `download_model.py`。Eagle 里的文件夹名在 `common.py` 里改。

## 进度

做完了前两步：建索引、检索和风格分类。之后计划用真实任务检索 → 分析 → 人工确认 → 写成审美档案 → 做成 Skill。审美结论会经过人工确认再写进档案，不让 AI 替人总结。
