# eagle-aesthetic：Eagle 个人审美系统（未完成）

照 @Sutao_1324 那篇「Eagle × SigLIP2 × Agent」的文章，给 Eagle 素材库建一个能按「感觉」找图的审美系统。2026-10-01 开始，本机目录 `~/claude/eagle-aesthetic`。

- 范围：Eagle 库「思想的记录」里的「海报排版」文件夹，约 8,400 张
- 模型：`google/siglip2-so400m-patch14-384`，图和文字映射到同一个向量空间，可以用一句话找图
- **对 Eagle 只读**：通过 Eagle 本地 API（`localhost:41595`）读，不打标签、不移动文件

## 脚本

| 文件 | 干嘛的 |
|---|---|
| `common.py` | Eagle 本地 API、模型加载、索引读写的公共函数 |
| `download_model.py` | 从 Hugging Face 分块并行下载模型到 `models/`，能断点续传 |
| `build_index.py` | 给「海报排版」里的图算向量，存到 `index/`；增量，已经算过的跳过 |
| `search.py` | 找图：一句话描述、一张参考图，或者「和某张图像的」；`--sheet` 出缩略图拼版，`--open N` 在 Eagle 里打开，`--json` 给 Agent 调用 |
| `classify.py` | 用已经分好风格的图当样本，给「北欧设计/原始文件」里没分类的图推荐风格。只出清单（`reports/classify.csv`），不写回 Eagle |

```bash
.venv/bin/python search.py "大面积留白、只有一行小字的海报" --sheet
```

依赖：torch、transformers、numpy、Pillow、scikit-learn。模型（4.3G）、虚拟环境、索引和 reports 都没放进仓库。

## 进度

文章的前两步（建索引、检索 + 风格分类）已跑完。第 3–8 步（拿真实任务检索 → 分析 → 自己确认 → 写审美档案 → 反馈 → 做成 Skill）还没开始。审美结论要自己确认后才写进档案，不让 AI 替我总结。
