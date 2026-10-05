# Skills, Agents and Prompts

马自立自己写的（或者魔改过的）Claude skill、agent 和提示词，备份在一处，免得忘了每个是干嘛的。

大部分东西的正本在本机各处，这里是副本：改了之后跑 `./sync.sh "改了什么"`，会从本机重新复制、提交、推送。只有 `prompts/claude-project-*.md` 是从 claude.ai 云端抄下来的，要手动更新。

---

## skills/：单个 skill

装在 `~/.claude/skills/`，任何目录下启动 Claude Code 都能用。

| skill | 干嘛的 | 什么时候触发 |
|---|---|---|
| [koubo-writer](skills/koubo-writer) | **写稿流水线**：一个选题 → 从主库「马自立」语义检索日记和笔记备料 → 素材不够先追问 → 定一句话主张、骨架、情绪线 → 按自己的风格提示词成稿，同时定好每段的画面（B-roll、插画、字卡）→ 机械检查 + 自查 → 存进稿子库并回链选题页。`scripts/sem_search.py` 按意思检索主库，`scripts/script_lint.py` 检查稿子 | 「写口播稿」「出一版稿」「把这个选题写出来」「再来一版」 |
| [vault-ask](skills/vault-ask) | **问自己的笔记**：在主库「马自立」里跨笔记问答、用笔记素材写提纲，结论都带可点的 `[[双链出处]]`，结果存回库里 | 「我记过哪些关于 X 的」「我对 Y 的看法怎么变的」「翻翻我的日记」 |
| [wardrobe-intake](skills/wardrobe-intake) | **衣橱入库**：把自己已经有的衣服、鞋、配饰登记进主库的 `穿搭/衣橱/`，一件一张卡片。想买的不进 | 发衣服照片或购买链接，说「入库」「记进衣橱」；日记里带 `#衣橱` 的块 |
| [gudianshi-skill](skills/gudianshi-skill) | **古典式配图**：给口播稿、文章画「古典质感 + 现代之刺」风格的解释图，版画、多雷 / 丢勒式插画加现代元素，只出 1600×900 的 SVG | 「古典式」「给稿子配图」「做个概念图 / 封面」 |

`gudianshi-skill` 是在 claude.ai 上建的，本机那份是桌面端自动同步下来的（`~/.claude/skills/synced/…`），改要去 claude.ai 改。

---

## agents/：一套组合（工作区配置、多个 skill、代码）

### [writing-agent](agents/writing-agent)：写稿 agent

不是单独的程序，是「稿子库 + koubo-writer + 风格提示词」这一套：

- `CLAUDE.md`：稿子库 `~/Documents/Obsidian Vault` 的工作规则。这个库只放正在写和写完的稿子；它和主库「马自立」怎么互相链接（选题页的 `稿件:`、稿子的 `素材:`）；在这里写稿用 `koubo-writer`；新版本另存不覆盖；AI 写的稿子标 `作者: AI 初稿`，不能当成本人文风样本
- 写稿流程本身在 [skills/koubo-writer](skills/koubo-writer)
- 文风约束在 [prompts/](prompts) 里的几份风格提示词

在 `~/Documents/Obsidian Vault` 里启动 Claude Code 就是这个 agent。

### [aigc-workspace](agents/aigc-workspace)：生图 / 生视频 / 角色设定

`~/claude/aigc` 工作区的配置，在那个目录里启动 Claude Code 才会加载这几个 skill：

| skill | 来源 | 干嘛的 |
|---|---|---|
| `character-sheet` | 自己写的 | 把参考图或角色描述做成锁定角色一致性的设定板 prompt（三视图、表情、服装细节等） |
| `cinematic-director` | 第三方 wuwangzhang1216/DirectorSKILL（MIT），**魔改**：加了杜琪峰导演风格 `director_styles/21_johnnie_to.md` 和中文视觉词汇表 `visual-vocabulary-zh.md` | 把剧本 / 一段文字 / 一张关键帧变成完整的拍摄计划：节拍、分镜、走位、镜头表、关键帧和视频 prompt |
| `image`、`video` | 第三方 smixs/visual-skills（CC-BY-4.0，要署名） | 按具体模型（GPT Image、Nano Banana、Seedance、Kling、Veo…）写生图 / 生视频提示词 |

`references/seedance2-storyboard/` 是参考资料（不自动加载）：从下载的 Seedance2 分镜工作流挪过来的可套用提示词、宫斗短剧和燕青打擂台的分镜 / 剧本示例，还有一个**没启用**的 `seedance-storyboard-generator` skill，因为它和 `video` 的触发场景重叠。

生成出来的角色卡和短片（`character-sheets/`、`shorts/`）没放进来。

### [eagle-aesthetic](agents/eagle-aesthetic)：Eagle 审美系统（未完成）

用 SigLIP2 给 Eagle 里「海报排版」的约 8,400 张图建向量索引，能用一句话或一张参考图按「感觉」找图，并给没分类的图推荐风格。对 Eagle 只读。照一篇文章的 8 步流程做，目前做完前两步。详见[它的 README](agents/eagle-aesthetic/README.md)。

### [invest-agent](agents/invest-agent)：股票分析

自己写的（2026-04）：FastAPI 小服务，输入 A 股 / ETF 代码 → AkShare 拉行情和财务 → GPT 分别做走势 / 财务分析和风险评级 → 渲染成带表格和图的网页报告。目录里另外 7 个 deep-research skill 是从下载的 `Claude-Code-Stock-Deep-Research-Agent` 原样复制的，**不是自己的**，没传。详见[它的 README](agents/invest-agent/README.md)。

### [openai-rag](agents/openai-rag)：OpenAI File Search（基本不用了）

自己写的（2026-04）：把 Markdown / PDF 传到 OpenAI 向量库，再对它们提问。现在查笔记用 vault-ask，比它好用，留着只当 RAG 的最小示例。详见[它的 README](agents/openai-rag/README.md)。

---

## prompts/：提示词

| 文件 | 用在哪 | 内容 |
|---|---|---|
| [claude-project-文章稿.md](prompts/claude-project-文章稿.md) | claude.ai 的 Project「文章稿」的 instructions | 自媒体稿子的写法：不煽动焦虑、要有活人感、核心论点加粗、术语不稀释但第一次出现要解释；每篇至少一处辛辣嘲讽、一处设问、一处自我反驳（devil's advocate）；外国人名和术语括号标英文，论文标作者和年份，结尾单列「信源」；文章框架和去矫饰的要求 |
| [口播稿风格提示词.md](prompts/口播稿风格提示词.md) | koubo-writer 写口播稿、播客稿时读 | 口播的文风约束。和书面语那份不通用 |
| [书面语风格提示词.md](prompts/书面语风格提示词.md) | koubo-writer 写博客、长文、Newsletter 时读 | 例句全部出自自己手写的 20 篇博文（8.4 万字） |
| [文稿风格提示词.md](prompts/文稿风格提示词.md) | 通用写稿约束 | 从稿子库那 13 篇成稿反推出来的。注意那批成稿很多是 AI 生成的（口播稿那份里有说明），文风以上面两份为准 |
| [股票研究八步提示词.md](prompts/股票研究八步提示词.md) | 研究一家公司时按顺序问 | 事实底座 → 行业好坏 → 怎么赚钱 → 财务质量 → 股权与治理 → 多空分歧 → 估值与护城河 → 汇总成一次 Deep Research。**别人写的**，从下载的股票尽调仓库（MIT）里抽出来的 |

三份风格提示词的正本在主库「马自立」的 `写作与创作/`，koubo-writer 每次写稿都会重新读，改那边就行。股票研究那份只存在这个仓库里，直接改这里。

---

## 本机 `~/Documents/agents`：agent 统一管理

2026-10-06 整理过一次：下载来试过就没再用的删了（移到了废纸篓 `agents-cleanup-20261006`），有用的部分抽出来放进了这个仓库，剩下的分成两组。

```
~/Documents/agents/
├── 自己写的/
│   ├── invest-agent/              → 本仓库 agents/invest-agent（sync.sh 同步）
│   ├── openai-rag/                → 本仓库 agents/openai-rag（sync.sh 同步）
│   └── linuxdo-社区内容分析/       一次性的数据分析：用 Qwen 分析 linux.do 社区帖子的互动数据，有图表和 HTML 报告。不是 agent，没进仓库
└── 下载的参考/
    └── claude-data-analysis-main/ 别人的：用 6 个分工子 agent + 斜杠命令 + 校验 hook 做数据分析。和装好的 csv-data-analysis、data-analyse 重复，只当「多 agent 怎么分工」的参考
```

以后再下载新的 agent，放进 `下载的参考/`；自己写的放进 `自己写的/`，并在 `sync.sh` 里加一行。

**2026-10-06 处理掉的：**

| 原来的 | 怎么处理的 |
|---|---|
| Claude-Code-Stock-Deep-Research-Agent | 自带的 276 份研报都不是自己跑的；提示词抽成 [股票研究八步提示词](prompts/股票研究八步提示词.md)，原目录删 |
| Seedance2-Storyboard-Generator | 提示词、示例和它带的 skill 挪进 aigc 的 `references/seedance2-storyboard/`，原目录删 |
| datalogic | 《数据分析咖哥十话》的配套课程，挪到 `~/Documents/005书库与声音库/`；里面自己做的 linuxdo 分析挪到 `自己写的/` |
| crewai_stock_analysis_system | 删：依赖一年多前的老版本 CrewAI，功能被别的股票项目覆盖 |
| semiconductor_agent | 删：针对卓胜微的工厂调研 demo，数据全是模拟的，没留下产出 |
| self-improving-agent（连同 `~/.learnings/`） | 删：没用起来，`~/.learnings/` 里只有空模板；Claude Code 自带记忆 |
| dataset_info.json | 删：LLaMA-Factory 的数据集登记表，对应数据都不在 |
| invest-agent、openai-rag 的虚拟环境 | 删，约 1.1G，要跑时重新装 |

---

## 本机还有、但没放进来的

- `~/.claude/skills/` 里其余的 skill（superpowers 系列、chatcut-*、obsidian-*、csv-data-analysis、akshare-stock、us-stock-analysis 等）都是装的别人的
- `~/claude/BoomEarth/.claude/skills/` 是克隆的开源项目 kaiteJiang/BoomEarth
- claude.ai 上另外两个 Project「书面稿」「投资」目前没有 instructions
