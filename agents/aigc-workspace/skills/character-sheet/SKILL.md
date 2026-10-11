---
name: character-sheet
description: 角色设定板（Character Sheet）提示词制作。把参考图或角色描述变成一份锁定角色 ID 的高精度设定板 prompt（4:3 横版，含三视图、剪影、8 表情、5 微表情、头部结构、姿态、特写、服装细节、手部动作），可拆出单独的表情板（3×3 面部研究）和状态板（同一个人的几种精神状态）。表情一律按低强度写肌肉动作和不动的部位，专门防生图模型把表情做夸张、做出 AI 味。当用户说"角色卡""角色设定板""character sheet""三视图""角色设定图""锁定角色一致性""做个角色""表情板""表情设定""表情太夸张""状态板"时使用。
---

# 角色设定板（Character Sheet）制作

目标：产出一份可以直接贴进生图模型（GPT Image / Nano Banana / Midjourney / 即梦 / Seedream 等）的角色设定板 prompt，核心是**锁定同一个角色**，所有模块不漂移。

模板文件：
- 中文版：`templates/prompt-template.md`
- 英文版：`templates/prompt-template.en.md`（多数生图模型对英文 prompt 更稳，默认两版都给）
- 表情板 / 状态板 + 默认 8 表情的低强度写法：`templates/expression-state-boards.md`

## 流程

### 1. 收集参数

需要以下字段。用户已经给了的直接用，没给的**一次性**问完（用 AskUserQuestion，不要逐条追问）；用户说"你定"就按合理默认补全。

| 字段 | 可选值 / 说明 | 默认 |
|---|---|---|
| 参考图 | 本地图片路径，可无 | 无 |
| 风格 STYLE | 写实3D / 风格化3D / 动漫 / 半写实 / IP设计 | 半写实 |
| 角色描述 DESCRIPTION | 外貌、服装、气质 | 参考图提取 |
| 性别 GENDER | 男 / 女 / 中性 | 参考图判断 |
| 年龄 AGE | 数值 | 参考图估计 |
| 体型 BODY_TYPE | 瘦 / 标准 / 健壮 / 夸张比例 | 标准 |
| 风格关键词 STYLE_KEYWORDS | 高级感 / 时尚 / 潮流 / 科技感 / 情绪化 等 | 按描述推断 |
| 背景 BACKGROUND | 纯白 / 米白 / 极简 | 米白 |

以下字段由你自动生成（用户指定则用用户的）：名字 NAME、角色身份 IDENTITY、性格关键词 PERSONALITY（3–5 个）、核心主题 THEME（1 句）、特写情绪 CLOSEUP_EMOTION（写成肌肉动作，见下面「表情防夸张」）、配色提示 PALETTE_HINT、表情组 EXPRESSION_SET / EXPRESSION_SET_EN（见第 2 步）。

### 2. 生成角色 ID 锁定段（最关键）

**先看有没有现成的人物精细描述**（`juese-sheji` 模式 E 的产出，`shorts/<项目>/人物精细描述-<角色>-v*.md`，或用户在聊天里刚做完的）：有的话，`{{CHARACTER_LOCK}}` 直接用它的生图锁定段「主设定」，不要重写、不要改动选定的写法（主设定里身份层在前、造型层在后：设定板的服装就是这一套造型，也就是 Look A；以后换装只换造型层，身份层永远照抄）；设定板里的特写、表情、手部模块再接上「特写细节」。它有「⑤ 表情谱」时，`{{EXPRESSION_SET}}` / `{{EXPRESSION_SET_EN}}` 直接用表情谱（那是这个人自己的表情，强度上限也按它来）；没有时用 `templates/expression-state-boards.md` 里默认的 8 个低强度表情。用户只给了「轻佻」「清冷」这类模糊感觉、又没有精细描述时，建议先走 `juese-sheji` 模式 E。

没有现成描述时：有参考图时，先用 Read 看图，再写出 `{{CHARACTER_LOCK}}`：一段具体、可复现的外观清单，逐项写实，不用形容词糊弄：

- 脸型、五官特征（眼型、眉形、鼻、唇、痣/疤等辨识点）
- 肤色
- 发型：长度、分线、颜色、质感
- 身高比例（几头身）、肩宽、体态
- 服装：每一件的款式、颜色、材质、版型
- 配饰、鞋
- 从参考图提取的 6–8 个主色（写成 HEX，填进 PALETTE_HINT，例如 `参考色：#1E1E24 #C8B6A6 ...`；设定板里色块本身仍不带文字）

没有参考图时，根据描述**先定稿**一个同样颗粒度的锁定清单，让用户确认后再往下走（这是后续一致性的基准）。

锁定段末尾固定加一句：`以上特征在所有模块中保持完全一致，不得修改。` / `Keep all of the above identical across every panel.`

### 表情防夸张

生图模型的表情普遍偏夸张：一笑露两排牙、一惊讶 O 形嘴、一难过挂眼泪，这是 AI 味最重的地方之一。设定板里所有表情（表情系统、微表情、特写、表情板）都按这几条写：

1. **不写情绪名，写肌肉动作 + 幅度**：`happy` → `the corners of the mouth lift slightly, lips together`。幅度用 barely / slightly / clearly，写实风格默认 barely–slightly，最多 clearly。
2. **写出不动的部位**：笑写清眉毛和眼睛怎样，难过写清嘴怎样，惊讶写清嘴只张开几毫米。这是最有效的一条。
3. **每格只动一两处**，其余保持默认表情；允许左右不对称。
4. **模型会放大一到两级**：想要 slightly 就写 barely。
5. **换成写实影像语境**：不用 `expression sheet` `emotions` `expressive` `dramatic`；用 `facial study` `subtle facial variations` `like frames from an understated live-action film`。模板里的【表情写法】段已经写好，不要删。
6. 动漫 / IP 风格可以整体提高一级，但仍然写肌肉动作。

完整版（A–E 强度分级、换词表、审图征兆）见 `juese-sheji` 的 `references/expression-restraint.md`。

### 3. 填模板

读取两个模板，替换全部 `{{...}}` 占位符，不要删改模块结构。检查：没有残留的 `{{`。

### 4. 保存并交付

- 保存到 `character-sheets/<角色英文名-小写连字符>/prompt.md`（相对 aigc 根目录），文件内依次放：参数表、中文 prompt、英文 prompt。有参考图就把图复制一份到同目录 `reference.<ext>`。
- 在回复里直接给出英文版 prompt（代码块，方便复制），并附文件链接。
- 提醒使用要点：
  - 生图时**同时上传参考图**，比例设 4:3；
  - 模块很多，单张图模型可能挤不下细节，可以拆成「主设定板」+「表情板」+「细节板」三张，每张都带同一段 CHARACTER LOCK；表情板用 `templates/expression-state-boards.md`（3×3，中间一格是默认表情，表情谱不足 9 个时用侧面补齐）；
  - 有弧光的主角可以加一张**状态板**（同一个人、同一套衣服，只换精神状态，3–4 格半身），模板也在那个文件里，状态的写法用 `juese-sheji` 的 `references/dimensions/09-精神状态.md`；
  - 表情出来以后逐格查夸张（露两排牙、O 形嘴、挂眼泪、全脸同时动）和换脸（和默认表情那格比下颌、眼睛大小），有就降一级、补不动的部位或单格重出；
  - 需要拆分时，按用户要求再输出拆分版。

### 5.（可选）直接生图

只有用户明确要求"直接生成图片"时才做：检查当前会话有没有可用的生图工具/skill（如 chatcut-image-gen），有则用英文 prompt + 参考图、4:3 生成，把结果存到同一角色目录；没有就说明并停在 prompt 交付。

## 注意

- 不允许为了"更好看"改动参考图里的角色特征。
- 一个角色一个目录；同一角色迭代时覆盖或追加 `prompt-v2.md`，不要新建角色目录。
