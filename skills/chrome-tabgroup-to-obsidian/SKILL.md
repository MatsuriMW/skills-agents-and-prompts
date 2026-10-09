---
name: chrome-tabgroup-to-obsidian
description: 把 Chrome 里保存的标签组（Tab Groups）导出成 Markdown 清单，归类为视频/文章、查作者、抽关键词双链，并按 SuperTags（自用）插件的字段键名填进 Obsidian 库。别名 / 触发词：chrometoob、chrometoobsidian、chrome2obsidian、chrome2ob、chrome to obsidian、标签组导出、tabgroup-to-obsidian、tabgroup to obsidian。当用户说「把 Chrome 标签组 X 整理到 Obsidian」「导出我的标签组」「把待看/待读的标签页收进库里」时使用。
---

# Chrome 标签组 → Obsidian 笔记

把一个 Chrome 标签组（例如「商业分析」）里的视频和文章整理成一篇 Obsidian 笔记：
嵌套无序列表 + 原始链接 + 关键词双链 + 作者 + SuperTags 字段。

## 什么时候用

用户说「把 Chrome 标签组 X 整理到 Obsidian」「导出我的标签组」「把待看/待读的标签页收进库里」——
任何要从 Chrome Tab Groups 往知识库搬内容的场景。

也会被这些名字 / 别名直接叫到（看到任何一个就该用本 skill）：
`chrome-tabgroup-to-obsidian` · `chrometoob` · `chrometoobsidian` · `chrome2obsidian` ·
`chrome2ob` · `chrome to obsidian` · `标签组导出` · `tabgroup to obsidian`。

## 关键事实（最容易搞错的地方）

- Chrome 的**已保存标签组不写在** `Sessions/*.SNSS` 里（那些只是当前/最近窗口的会话快照）。
  真正的来源是 `Sync Data/LevelDB`，键前缀 `saved_tab_group-dt-<guid>`。
- 那个 LevelDB 的 SSTable 用 **Snappy 压缩**，标准库和常见第三方库读不了，**必须**用本 skill 自带的
  `scripts/read_chrome_tabgroups.py`（纯标准库实现：Snappy 解压 + SSTable/WAL 解析 + protobuf 最小解码）。
  别再从头写一遍，也别指望用 `plyvel`/`leveldb` 之类的包（要编译，且不一定装得上）。
- value 长度为 0 的 key 是**墓碑（已删除）**，必须过滤掉，否则会拿到一堆空条目。
- macOS 上用 AppleScript 控制 Chrome 会报 `privilege violation (-10004)`（未授权自动化），
  别在这个方向浪费时间，直接读数据库。

## 默认环境（每次开头跟用户确认一句，允许覆盖）

- Obsidian 库：**马自立**
  `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立`
  收藏类笔记放 `阅读收藏/`。缩进用 **Tab**（该库既有笔记的惯例）。
- SuperTags 插件：**SuperTags（自用）** = 插件目录 `supertags-local`（原版 `supertags` 是未启用的）。
  配置在 `马自立/.obsidian/plugins/supertags-local/data.json`。
- Chrome 用户数据目录：`~/Library/Application Support/Google/Chrome`（脚本会自动探测，多 profile 也扫）。
- 验证自己看的是不是「自用」版：`community-plugins.json` 里应只有 `supertags-local`；
  且它的 `data.json` 里有 `#towatch`/`#toread`（原版只有 `#concept`/`#book`）。

## 工作流

1. **读标签组**
   ```bash
   python3 scripts/read_chrome_tabgroups.py --list-groups          # 先看有哪些组
   python3 scripts/read_chrome_tabgroups.py --group 商业分析        # 看某组
   python3 scripts/read_chrome_tabgroups.py --group 商业分析 --json # 要结构化数据
   ```
2. **清洗**：URL 去掉 `spm_id_from`、`vd_source`、`trackid` 等追踪参数，只留干净的 BV 号 / p/ 路径。
   标题去掉站点尾巴（`_哔哩哔哩_bilibili`、知乎的 `(99+ 封私信 / 3 条消息) `）。
   按 URL 判断类型：`bilibili.com/video`、`youtube.com/watch` → 视频；`zhuanlan.zhihu.com/p`、专栏、博客 → 文章。
3. **查作者**：见 `references/author-lookup.md`。B 站走官方 API 最稳；知乎常被反爬，用正文里的自引用兜底。
4. **关键词**：每条 1~2 个，写成 `[[关键词]]` 双链。先搜库里是否已有同名页面，没有才新建。
5. **打标签 + 填字段**：视频加 `#towatch`，文章加 `#toread`；字段见 `references/supertags-fields.md`。
6. **落库**：写成一篇汇总笔记（默认），文末附「作者索引」「关键词索引」。
   只有用户明确要求时才拆成每条目一个文件。

## 格式模板

```markdown
---
aliases:
  - X
tags:
  - 收藏/阅读清单
source: Chrome 标签组「X」
date: YYYY-MM-DD
---

# X（Chrome 标签组）

- 视频
	- 标题 #towatch
		- 链接：https://…
		- type:: 作品
		- 类别:: 视频（B站）
		- 清单:: [[towatch]]
		- 状态:: 想看
		- 作者:: [[小林说]]
		- def:: 一句话摘要
		- from:: [[本笔记名]]
		- 关键词：[[A]] [[B]]
- 文章
	- 标题 #toread
		- 链接：https://…
		- type:: 文章
		- 清单:: [[toread]]
		- 状态:: 想读
		- author:: 作者名
		- def:: 一句话摘要
		- domain:: [[主题]]
		- from:: [[本笔记名]]
		- 关键词：[[A]] [[B]]
```

## 规则 / 常见坑

- 字段一律用**子项 `键:: 值`** 写法（插件的 `CHILD_FIELD_RE` 认这个），不要用 `键: 值`。
- 键名要跟插件模板**逐字一致**：`#towatch` 用 `作者`，`#toread` 用 `author`（一个是中文一个是英文，别互换）。
- 属性值里放双链是可以的（`作者:: [[小林说]]`），但键本身不能含 `:：[]#`。
- `#toread` 的 `type` 可选 书 / 文章 / 论文，文章填 `type:: 文章`。
- 插件 `watchFolders` 通常只有 `日记/`——放在 `阅读收藏/` 的笔记**不会**被自动处理成新页面，
  字段只是「预先填好」。这条也要提醒用户。
- `#towatch` / `#toread` / `#tolisten` 都设了 `fields`（2026-10-10 起），键名要把 `frontmatterTemplate` 和 `fields` 两处合起来读；
  有可选值的（`# 后面`）从里面挑。改插件配置前先问用户。
- 摘要（`def`）只写基于标题/页面可见信息能支撑的内容，别编造视频里讲没讲过什么。

## 完成前自查

- [ ] 条目数和标签组实际数量一致（对照 `--list-groups` 的计数）。
- [ ] 每个视频有 `#towatch`、每篇文章有 `#toread`。
- [ ] 每个条目下方字段键名与插件模板一致，没有漏键。
- [ ] 双链都是 `[[]]`，且指向的页面确实存在或确实该新建。
- [ ] URL 已去掉追踪参数，标题已去掉站点尾巴。
- [ ] 已提醒用户 watchFolders 这个偏离点（放在 日记/ 以外不会自动建页）。

## 附带文件

- `scripts/read_chrome_tabgroups.py` —— 读 Chrome 同步数据库里的已保存标签组（**核心，别删**）。
- `references/author-lookup.md` —— 各站点查作者的可靠办法。
- `references/supertags-fields.md` —— SuperTags 字段怎么读、键名对照。
- `RUNBOOK.md` —— 自包含说明书（含脚本全文），贴给别的 AI 也能照做。
