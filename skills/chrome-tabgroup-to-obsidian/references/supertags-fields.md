# SuperTags（自用）字段速查

## 先确认你在看哪个插件

库里可能同时存在两个：

| 目录 | id | 插件名 | 典型状态 |
|---|---|---|---|
| `.obsidian/plugins/supertags-local` | `supertags-local` | **SuperTags（自用）** | 已启用 |
| `.obsidian/plugins/supertags` | `supertags` | SuperTags（原版） | 未启用 |

判据：`<库>/.obsidian/community-plugins.json` 里列出的是已启用的；再看 manifest 的 `name` 字段。
两份 `data.json` 内容也不同——原版通常只有 `#concept`/`#book`，自用版才有 `#towatch`/`#toread`。

## 字段从哪来

每个 supertag 有这几个配置项：`tag` / `folder` / `frontmatterTemplate` / `fields` / `bodyTemplate`。

- `fields`（`键: 默认值 # 可选值1, 可选值2`，一行一个；`#` 后面是可选值，可以没有）：
  设了 `fields` 的标签，「日记整理」会把这些字段插到 `[[标签名]]` 下面；
  待读 / 待看 / 待听看板（`scripts/marker-board.js`）也按它们显示维度、筛选。
- `frontmatterTemplate`：新建页面时写进 frontmatter 的其余键（清单 / def / from 等）。

**键名 = `frontmatterTemplate` 的键 + `fields` 的键**，两处都要读。有可选值的字段，填值时从可选值里挑。
2026-10-10 起 `#towatch` / `#toread` / `#tolisten` 都设了 `fields`。

## 键名对照（自用版配置，以实际 data.json 为准）

**`#towatch` / `#待看`**（folder 影视与音乐/）
```
frontmatterTemplate:
type: 作品
清单: "[[towatch]]"
def:
from: "[[{{source}}]]"
fields:
类别: # 电影, 剧集, 纪录片, 动画, 视频（B站）, 视频（YouTube）
状态: 想看 # 想看, 在看, 已看
作者:
```

**`#toread` / `#待读` / `#book`**（folder Books/）
```
frontmatterTemplate:
清单: "[[toread]]"
def:
from: "[[{{source}}]]"
fields:
type: 书 # 书, 文章, 论文
状态: 想读 # 想读, 在读, 已读
author:
domain: []
```
文章填 `type:: 文章` 是正式可选值，不再是偏离。

**`#tolisten` / `#待听`**：同 `#towatch`，`清单: "[[tolisten]]"`，`类别` 可选 播客 / 有声书 / 音乐 / 课程 / 视频（B站），`状态` 想听 / 在听 / 已听。

注意 `作者`（待看 / 待听）vs `author`（待读）一个中文一个英文，**别互换**。

## 写法

字段要写成列表子项，插件的 `CHILD_FIELD_RE` 才认：

```markdown
- 标题 #towatch
	- 作者:: [[小林说]]
	- 状态:: 想看
```

也支持行内 `[键:: 值]` 和 `#键/值`（如 `#选题/草稿` 记作 `状态`）。
键名本身不能包含 `:` `：` `[` `]` `#`，长度别超过 16。

## 其它机制要点

- `watchFolders` 默认只有 `日记/`——只有这个目录下的文件会被自动处理并建新页面。
  放在别处的笔记只是「预先填好字段」，不会触发建页。
- 标签是**边界匹配**：`#选题` 不会命中 `#选题/草稿`。中文紧邻也 OK。
- 同名笔记已存在（库里任何位置）时不新建，字段写进那篇、子项追加到末尾。

## 想改配置时

改 `fields` / 可选值是改用户的插件配置，**动之前先问**。改完要重载 supertags-local 插件才生效。
