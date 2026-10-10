# Skills, Agents and Prompts

马自立（[@MatsuriMW](https://github.com/MatsuriMW)）自己写的、或者改过的 [Claude Code](https://claude.com/claude-code) skill、agent 和提示词，主要用来**写作**（文章、口播稿）、**整理自己的笔记**，外加几个 AI 生图和投资研究的小项目。

这些东西本来是为我自己的 Obsidian 库和写作习惯做的，所以分成两类看：

- **可以直接拿去用的**：古典式配图、写作纪律、风格提示词、股票研究提示词，换个人也照样能用。
- **可以参考着改的**：写稿流水线、笔记问答这些 skill，里面写死了我的库路径和目录约定。它们最有价值的是**流程设计**：怎么从自己的笔记里找素材、怎么定主张和骨架、怎么做机械检查。换成你的库路径就能跑。

## 推荐度怎么看

| 推荐度 | 意思 |
|---|---|
| ★★★ | 通用，装上就能用 |
| ★★ | 能用，但要准备一点东西（API key、自己的风格文档、某个工具） |
| ★ | 和我的库结构绑得比较深，更适合当参考、改成你自己的版本 |

---

## skills/：单个 skill

装法：把目录复制到 `~/.claude/skills/`（所有项目都能用）或某个项目的 `.claude/skills/`，重开 Claude Code 会话。

| skill | 作用 | 推荐度 | 需要什么 |
|---|---|---|---|
| [gudianshi-skill](skills/gudianshi-skill)（古典式配图） | 给文章、口播稿画「古典质感 + 现代之刺」风格的解释图：版画、多雷 / 丢勒式插画，配一处现代元素制造反差。只输出 1600×900 的 SVG 矢量图，可以直接改。[`examples/`](skills/gudianshi-skill/examples) 里有 7 张成品可以先看效果；SkillHub 上也能装（slug `gudianshi`） | ★★★ | 无 |
| [human-writing](skills/human-writing)（写作纪律，改版） | 通用的中文写作和改稿纪律：材料不够不灌水、事实要核、不写空洞的翻案腔。改自一个 MIT 协议的第三方 skill：去掉了黑话禁词表、「排比最多三项」和破折号 / 冒号的禁令，加了「多用强逻辑结构表达」 | ★★★ | 无 |
| [wenzhanggao](skills/wenzhanggao)（文章稿） | 写文章、改文章的完整流程：按一份风格提示词写（暴论开头、设问、自我反驳、核心论点加粗、外国术语标英文、文末列信源），从选题写时先去笔记里找素材 | ★ | 一份你自己的风格提示词；Obsidian 库 |
| [koubo-writer](skills/koubo-writer)（口播稿流水线） | 一个选题 → 按意思检索自己的日记和笔记备料 → 素材不够先追问 → 定一句话主张、骨架和情绪线 → 成稿，同时规划每段的画面（B-roll、插画、字卡）→ 机械检查 → 存回库里。带两个脚本：`sem_search.py` 语义检索笔记，`script_lint.py` 检查稿子 | ★ | Obsidian 库；本机 Ollama + EmbeddingGemma（和 [第二大脑](https://github.com/MatsuriMW/Obsidian-Plugins/tree/main/second-brain) 插件共用向量缓存） |
| [vault-ask](skills/vault-ask)（问自己的笔记） | 在 Obsidian 库里跨笔记问答、用笔记素材写提纲，每个结论都带可点击的 `[[双链出处]]`，结果存回库里 | ★ | Obsidian 库 |
| [wardrobe-intake](skills/wardrobe-intake)（衣橱入库） | 发一张衣服照片或购买链接，登记成库里的一张衣橱卡片：品类、颜色、材质、图案等字段按模板填，信息不够的留空、不乱猜，最后告诉你还要补什么 | ★ | Obsidian 库 |
| [chrome-tabgroup-to-obsidian](skills/chrome-tabgroup-to-obsidian)（Chrome 标签组入库） | 把 Chrome 里保存的标签组导出成一篇 Obsidian 笔记：视频 / 文章分块、去追踪参数的干净链接、关键词 `[[]]` 双链、查作者，并按 SuperTags 标签的字段键名填 `键:: 值`。带一个纯标准库的脚本 `read_chrome_tabgroups.py`，直接读 Chrome 同步数据库（LevelDB + Snappy），是整套流程的关键。详见下面 [单独一小节](#chrome-tabgroup-to-obsidian把攒着的标签页变成一篇笔记) | ★★ | Chrome（标签组要保存过）；Obsidian 库（要改路径）；SuperTags 插件可选 |

**写作类 skill 的分工**：`wenzhanggao` 是默认的写作 skill，所有书面稿都按它的风格提示词写；`koubo-writer` 只在要做成视频时叠加口播的要求；`human-writing` 只当通用纪律。三者冲突时按这个顺序。

### chrome-tabgroup-to-obsidian：把攒着的标签页变成一篇笔记

**它解决什么**。浏览器里攒了一个标签组（比如「商业分析」），十几个视频加文章，一关就再也找不回来。这个 skill 把整组一次性搬进 Obsidian：视频 / 文章分块、去掉追踪参数的干净链接、查作者、抽关键词做成 `[[双链]]`，最后落成一篇能直接翻的清单。

**难点在取数据，不在整理**。Chrome 的已保存标签组不写在 `Sessions/` 的会话文件里（那些只反映当前窗口，组一关就没了），而是在 `Sync Data/LevelDB`，且 SSTable 用 **Snappy 压缩**——标准库和常见的 leveldb 包都读不了。`scripts/read_chrome_tabgroups.py` 用纯标准库实现了 Snappy 解压 + LevelDB（SSTable / WAL）解析 + protobuf 解码，这是整套流程里唯一没法临时凑出来的部分，也是这个 skill 真正值钱的地方。

用法：

```bash
python3 scripts/read_chrome_tabgroups.py --list-groups            # 有哪些组
python3 scripts/read_chrome_tabgroups.py --group 商业分析          # 看某组
python3 scripts/read_chrome_tabgroups.py --group 商业分析 --json   # 要结构化数据
```

它会按组内的 `position` 还原原本的顺序，输出标题 + URL。之后交给模型做剩下的事：B 站走官方 `x/web-interface/view` 接口查 UP 主（免登录），知乎常被反爬，就用正文里的自引用兜底；视频打 `#towatch`、文章打 `#toread`；字段按 SuperTags 标签里 `frontmatterTemplate` + `fields` 两处的键名，写成列表子项 `键:: 值`。

产出大概是这个样子（缩进用 Tab）：

```markdown
- 视频
	- 【硬核】一口气了解外汇 #towatch
		- 链接：https://www.bilibili.com/video/BV1iW42197dP/
		- 类别:: 视频（B站）
		- 状态:: 想看
		- 作者:: [[小林说]]
		- def:: 一句话摘要
		- 关键词：[[外汇]] [[汇率]]
- 文章
	- 行业研究框架和 26 个常用商业模型 #toread
		- 链接：https://zhuanlan.zhihu.com/p/328076946
		- author:: yulang
		- 关键词：[[行业研究]] [[商业模型]]
```

**要改成你自己的**：`SKILL.md` 的「默认环境」写死了我的 Obsidian 库路径、`阅读收藏/` 目录和 SuperTags 插件的位置，换成你的即可；不用 SuperTags 就跳过填字段那一步，其余照常。所以推荐度是 ★★ 而不是 ★★★——脚本通用，但路径要自己填。

**已知边界**：

- 只认**已保存**的标签组（存在同步数据里的那种），临时开着的窗口会话不保证能取到。
- 插件的字段键名以你自己的 `data.json` 为准，SKILL 里记的是我的配置快照；插件改了要同步更新 `references/supertags-fields.md`。
- 插件的 `watchFolders` 一般只有 `日记/`，放在别处的笔记不会被自动处理成新页面——字段是「预先填好」，不是自动建页。

---

## agents/：一整套组合

| agent | 作用 | 推荐度 | 需要什么 |
|---|---|---|---|
| [writing-agent](agents/writing-agent) | 写稿 agent 的工作区规则（`CLAUDE.md`）：Obsidian 库里选题页和稿子怎么互相链接、什么时候用哪个写作 skill、AI 初稿怎么标注、新版本另存不覆盖。配合上面的写作 skill 和 [prompts/](prompts) 一起用 | ★ | 上面的写作 skill |
| [aigc-workspace](agents/aigc-workspace) | AI 短片前期的工作区：从剧本到分镜、角色设计、角色设定板，再到按具体模型写生图 / 生视频 prompt。包含自己写的 [角色设计 juese-sheji](https://github.com/MatsuriMW/ai-character-design-skill) 和 [角色设定板 character-sheet](https://github.com/MatsuriMW/aigc-skills-and-agents)，以及改过的导演 skill（加了杜琪峰风格和中文视觉词汇表）和第三方的生图 / 生视频 prompt skill | ★★ | Claude Code；生图 / 生视频平台 |
| [invest-agent](agents/invest-agent) | 输入一个 A 股或 ETF 代码，拉行情和财务数据，让 GPT 分别做走势分析、财务分析和风险评级，生成带表格和图的网页报告。FastAPI 小服务 | ★★ | Python；OpenAI API key |
| [eagle-aesthetic](agents/eagle-aesthetic) | 给 Eagle 素材库建「按感觉找图」：用 SigLIP2 把几千张海报做成向量索引，一句话或一张参考图就能找出气质相近的图，并给没分类的图推荐风格。对 Eagle 只读。**还没做完** | ★ | Python；Eagle |
| [openai-rag](agents/openai-rag) | 最小的 RAG 示例：把 Markdown / PDF 传到 OpenAI 的向量库，再对它们提问 | ★ | Python；OpenAI API key |

`aigc-workspace` 里的第三方 skill 按原许可证收录：导演 skill 来自 [wuwangzhang1216/DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL)（MIT，有改动），`image` / `video` 来自 [smixs/visual-skills](https://github.com/smixs/visual-skills)（CC-BY-4.0）。

---

## prompts/：提示词

| 提示词 | 作用 | 推荐度 |
|---|---|---|
| [文章稿风格提示词](prompts/文章稿风格提示词.md) | 我的写作风格总纲：不煽动焦虑、要有活人感、核心论点加粗、术语不稀释但第一次出现要解释，每篇至少一处辛辣嘲讽、一处设问、一处自我反驳；后半部分是细则和例句。可以当成写一份自己风格提示词的模板 | ★★ |
| [口播稿风格提示词](prompts/口播稿风格提示词.md) | 叠加在文章稿之上的口播要求：写给耳朵听、控制句子密度、录制标记、录前速查清单 | ★★ |
| [文白交杂风格提示词](prompts/文白交杂风格提示词.md) | 想让文字更文白交杂时的附加层：往前推到什么程度、哪些地方用文言 | ★★（草稿） |
| [股票研究八步提示词](prompts/股票研究八步提示词.md) | 研究一家公司时按顺序问的八步：事实底座 → 行业好坏 → 怎么赚钱 → 财务质量 → 股权与治理 → 多空分歧 → 估值与护城河 → 汇总成一次深度研究。**别人写的**，从一个 MIT 协议的股票尽调仓库里整理出来 | ★★★ |
| [claude-project-文章稿](prompts/claude-project-文章稿.md) | 文章稿风格提示词的早期版本，留作对照 | — |

---

## 相关仓库

- [ai-character-design-skill](https://github.com/MatsuriMW/ai-character-design-skill)：把「一个轻佻的男性」这种模糊感觉拆成生图模型能执行的描述，AI 短片的角色设计 skill（有安装脚本，可以直接交给别人用）
- [aigc-skills-and-agents](https://github.com/MatsuriMW/aigc-skills-and-agents)：角色设定板等 AIGC skill
- [Obsidian-Plugins](https://github.com/MatsuriMW/Obsidian-Plugins)：我做的 / 改过的 30 多个 Obsidian 插件，写作 skill 用到的本地语义检索就在里面
