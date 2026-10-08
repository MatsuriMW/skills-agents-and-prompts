# AIGC 工作区

AI 生成内容（生图 / 生视频 / 角色设定）相关任务的工作目录。

## 目录

- `.claude/skills/` — 本工作区专属 skill，只在 aigc 目录内启动 Claude Code 时加载
  - `character-sheet/` — 角色设定板（Character Sheet）prompt 制作
  - `juese-sheji/` — 角色设计（原 fuhuadao）：具体化（入口：把「轻佻的男性」这类模糊感觉拆成维度、写成名词和动作，`references/articulate-rules.md` + `references/dimensions/` 维度词库，分一般 / 深入两档，产出 `shorts/<项目>/人物精细描述-<角色>-v<N>.md`，示例 `examples/轻佻的男性.md`）、人物原型（`references/archetypes/` 里 122 个影视经典人物原型的图鉴，按「原型 + 具体 + 反转」本土化）、检验（时代考据、性格表达、记忆点、慎用套路，出评分和改法）、创意风暴（发散几个造型方向再收敛）、设计落地（Look / 妆发 / 道具 / 连戏表 + 生图锁定段）。产出存 `shorts/<项目>/人物原型-v<N>.md`、`服化道*-v<N>.md`
  - `cinematic-director/` — 分镜 / 导演流程（第三方 wuwangzhang1216/DirectorSKILL，MIT）。本地加了 `director_styles/21_johnnie_to.md` 和 `references/visual-vocabulary-zh.md`，更新上游时注意保留
  - `video/`、`image/` — 按模型写生视频 / 生图提示词（第三方 smixs/visual-skills，CC-BY-4.0）
  - 各第三方 skill 的来源和 commit 记在各自目录的 `.source`
- `exports/juese-sheji-chatcut/` — 角色设计 skill 的 ChatCut 版（去掉了本地路径，模板放在 references/templates/、示例放在 references/examples/）。已上传到 ChatCut「我的技能」，skill id `f9222f71-ea73-4b6f-ae98-89168edb03f1`；改了本地 skill 要同步这份再整包更新
- `references/` — 参考资料，不会自动加载，需要时去读
  - `seedance2-storyboard/` — 下载的 Seedance2 分镜工作流：可套用的提示词、宫斗短剧和燕青打擂台的分镜 / 剧本示例，外加一个未启用的 `seedance-storyboard-generator` skill。写 Seedance 分镜时可以翻
- `character-sheets/` — 每个角色一个子目录：`prompt.md`、`reference.*`、生成结果
- `docs/specs/` — skill 的设计文档
- `shorts/` — 短片项目，每部一个子目录：`README.md`（要做什么 + 资料索引）、`资料/`（原始素材副本）、分镜稿 / 场景稿按版本号迭代

## 约定

- 生成内容按任务类型分目录存放，不要散落在根目录。
- 同一角色的迭代放在同一目录下，用版本号区分。
