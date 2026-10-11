# 表情板与状态板

主设定板模块多、一张图挤不下时，把表情拆出来单独出一张**表情板**；有弧光的主角再加一张**状态板**。两张都带和主设定板**同一段** CHARACTER LOCK，并同时上传主设定板（或默认表情的正脸图）当参考图。

占位符：`{{CHARACTER_LOCK}}` 同主设定板；`{{CLOSEUP_DETAILS}}` 是 `juese-sheji` 人物精细描述里的「特写细节」，没有就删掉这一行；`{{EXPRESSION_SET}}` / `{{EXPRESSION_SET_EN}}` 见下一节，每个表情一行。

---

## 默认的 8 个表情（没有表情谱时用）

有 `juese-sheji` 的表情谱（人物精细描述里的「⑤ 表情谱」）时，`{{EXPRESSION_SET}}` / `{{EXPRESSION_SET_EN}}` 直接用它：那是这个人自己的表情，比通用表情准得多。没有时用下面这一组。全部是低强度写法：模型会把表情放大一到两级，所以这里故意写小。

| # | 表情 | 中文写法 | English |
|---|---|---|---|
| 1 | 平和 | 默认表情，脸部放松，嘴唇合着 | Resting: relaxed resting face, lips closed. |
| 2 | 开心 | 嘴角微微提起，嘴唇合着；外眼角出现浅浅的笑纹；眉毛不动 | Happy: the corners of the mouth lift slightly, lips together; faint creases at the outer eye corners; brows stay level. |
| 3 | 悲伤 | 眉毛内侧微微上抬，嘴角微微下沉；眼睛有一点湿；脸不皱 | Sad: inner brows faintly raised, mouth corners slightly lowered; eyes a little glossy; the face does not crumple. |
| 4 | 生气 | 眉头微微下压，嘴唇压紧变薄，下颌咬住；眼睛不瞪 | Angry: brows drawn down slightly, lips pressed thin, jaw set; eyes stay level. |
| 5 | 惊讶 | 眉毛微微上抬，眼睛比平时睁开一点，嘴唇分开几毫米 | Surprised: brows lift slightly, eyes open a little wider than resting, lips part a few millimetres. |
| 6 | 害怕 | 眼睛微微睁大，眉毛内侧上抬并往中间聚，嘴唇收紧往后拉一点 | Afraid: eyes slightly wider, inner brows faintly raised and drawn together, lips tightened and pulled back a little. |
| 7 | 紧张 | 嘴唇轻轻抿着，视线略往下，眉间有一点紧 | Nervous: lips lightly pressed together, gaze slightly lowered, a faint tension between the brows. |
| 8 | 坚定 | 眉毛平而微压，视线直，下颌收住，嘴唇合紧 | Determined: brows level and slightly lowered, steady direct gaze, jaw set, lips closed firmly. |

写法规则（完整版见 `juese-sheji` 的 `references/expression-restraint.md`）：
- 不写情绪名单词（happy、crying、shocked），写肌肉动作 + 幅度（barely / slightly / clearly）
- 写出**不动的部位**（眼睛怎样、眉毛怎样、嘴怎样）：这是防夸张最有效的一招
- 每格只动一两处，其余保持默认表情
- 不用 `expression sheet` `emotions` `expressive` `dramatic`，用 `facial study` `subtle facial variations` `like frames from an understated live-action film`

---

## 表情板（中文）

```
【任务】
为同一个角色生成一张面部研究板（facial study）。锁定角色 ID，不允许生成新角色，每一格都是同一个人。

【角色 ID 锁定】
{{CHARACTER_LOCK}}
{{CLOSEUP_DETAILS}}

【画面结构】
- 4:3 横版，3×3 九宫格，中间一格是默认表情（最大或用细框标出）
- 每格头肩构图，正面略偏 3/4，同一角度、同一光线（柔和的正面主光）、同一 {{BACKGROUND}} 背景
- 每格下方一行清晰的英文小标签（表情名），无 logo、无水印

【九格内容】
{{EXPRESSION_SET}}
（不足 9 格时，用默认表情的 3/4 侧和侧面补齐）

【表情写法】
- 所有表情都是克制、自然的低强度表情，像一部收着演的真人电影里的一帧；不是表演练习，不是表情包
- 每一格只改变写出来的那一两处，脸的其余部分保持默认表情；五官比例和特征在九格里完全一致
- 笑时嘴唇合着或只微张；难过时眼睛是干的、最多眼眶微红；惊讶时嘴唇只分开几毫米

【一致性要求】
- 九格是同一个人：脸型、五官、发型、肤色、痣和疤的位置完全一致
- 服装只露出领口，与主设定一致

【质量要求】
- 写实皮肤质感，保留毛孔和不完美
- 影视级柔光
```

## Expression board (English)

```
[TASK]
Create a facial study board for one character. LOCK the character identity: do not invent a new character; every panel is the same person.

[CHARACTER ID LOCK]
{{CHARACTER_LOCK}}
{{CLOSEUP_DETAILS}}

[LAYOUT]
- 4:3 landscape, 3×3 grid; the centre panel is the resting expression (largest, or outlined with a thin frame)
- Every panel head-and-shoulders, front to slight 3/4, same angle, same lighting (soft frontal key light), same {{BACKGROUND}} background
- A small, legible English label under each panel (expression name); no logo, no watermark

[PANELS]
{{EXPRESSION_SET_EN}}
(If there are fewer than 9 expressions, fill the remaining panels with the resting expression in 3/4 and profile.)

[EXPRESSIONS]
- Every expression is subtle and naturalistic, at low intensity, like a frame from an understated live-action film; not an acting exercise, not an emoji chart
- In each panel only the one or two described features change; the rest of the face stays at the resting expression; facial proportions and features identical across all nine panels
- Smiles keep the lips together or barely parted; sad faces stay dry-eyed, at most faintly red-rimmed; surprise parts the lips only a few millimetres

[CONSISTENCY]
- All nine panels are the same person: face shape, features, hairstyle, skin tone, and the positions of moles and scars identical
- Only the collar of the outfit is visible, matching the main sheet

[QUALITY]
- Realistic skin texture with pores and imperfections
- Cinematic soft lighting
```

---

## 状态板

同一个人、同一套服装、同一个角度和光，只换**精神状态**（例：平常 / 熬了一周 / 崩溃之后 / 走出来以后），用来在开拍前看清弧光，也给后面的镜头当参考图。状态的写法用 `juese-sheji` 的 `references/dimensions/09-精神状态.md`：每格只列这一档看得见的落点（眼周、气色、头发、衣服打理、姿态），不写 exhausted、depressed 这类状态名。

```
[TASK]
Create a state board for one character: the same person, the same outfit, the same camera angle and lighting, shown in {{N}} different states over the course of the story. LOCK the character identity.

[CHARACTER ID LOCK]
{{CHARACTER_LOCK}}

[LAYOUT]
- 4:3 landscape, {{N}} panels side by side (3 or 4), each waist-up, front-facing, same {{BACKGROUND}} background
- A small, legible English label under each panel; no logo, no watermark

[PANELS]
1. {{STATE_1_LABEL}}: {{visible markers: eyes and eye area, complexion, hair, how the clothes are worn, posture}}
2. {{STATE_2_LABEL}}: {{…}}
3. {{STATE_3_LABEL}}: {{…}}
4. {{STATE_4_LABEL}}: {{…}}

[RULES]
- Identity layer identical in every panel (face structure, features, build, permanent marks); only the listed state markers change
- Facial expressions stay subtle and close to the resting expression; the state shows through the eyes, skin, hair, clothes and posture, not through acted emotion
- Realistic skin texture, cinematic soft lighting
```

---

## 审图

- 逐格看有没有夸张：露两排牙、O 形嘴、挂眼泪、眉毛整体高抬、全脸同时动、左右完全对称、像表情包。有就降一级强度、补不动的部位，或者单格重出。
- 逐格和中间那格默认表情比：下颌、眼睛大小、鼻子有没有变。表情越大越容易换脸；九格漂得厉害就减到 6 格，或者用默认脸参考图逐格编辑。
