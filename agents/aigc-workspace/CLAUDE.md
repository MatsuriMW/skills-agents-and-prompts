# AIGC 工作区

AI 生成内容（生图 / 生视频 / 角色设定）相关任务的工作目录。

## 目录

- `.claude/skills/` — 本工作区专属 skill，只在 aigc 目录内启动 Claude Code 时加载
  - `character-sheet/` — 角色设定板（Character Sheet）prompt 制作
  - `juese-sheji/` — 角色设计（原 fuhuadao）：具体化（入口：把「轻佻的男性」这类模糊感觉拆成维度、写成名词和动作，`references/articulate-rules.md` + `references/dimensions/` 维度词库，分一般 / 深入两档，产出 `shorts/<项目>/人物精细描述-<角色>-v<N>.md`，示例 `examples/轻佻的男性.md`；风格库 `references/styles/`：47 个服装风格由 `scripts/sync-styles.py` 从主库 `审美/风格/` 生成，主库是正本，另有手写的「人群与身份」；出图后按 `references/drift-checklist.md` 审，各模型实测记进 `references/model-notes.md`，评测流程在 `evals/`）、人物原型（`references/archetypes/` 里 122 个影视经典人物原型的图鉴，按「原型 + 具体 + 反转」本土化）、检验（时代考据、性格表达、记忆点、慎用套路，出评分和改法）、创意风暴（发散几个造型方向再收敛）、设计落地（Look / 妆发 / 道具 / 连戏表 + 生图锁定段）。产出存 `shorts/<项目>/人物原型-v<N>.md`、`服化道*-v<N>.md`
  - `cinematic-director/` — 分镜 / 导演流程（第三方 wuwangzhang1216/DirectorSKILL，MIT）。本地加了 `director_styles/21_johnnie_to.md` 和 `references/visual-vocabulary-zh.md`，更新上游时注意保留
  - `video/`、`image/` — 按模型写生视频 / 生图提示词（第三方 smixs/visual-skills，CC-BY-4.0）
  - 各第三方 skill 的来源和 commit 记在各自目录的 `.source`
- `exports/juese-sheji-chatcut/` — 角色设计 skill 的 ChatCut 版（去掉了本地路径，模板放在 references/templates/、示例放在 references/examples/）。已上传到 ChatCut「我的技能」，skill id `f9222f71-ea73-4b6f-ae98-89168edb03f1`；改了本地 skill 后跑 `python3 exports/build-chatcut.py` 重新生成这份，再整包更新到 ChatCut（只能在 ChatCut Desktop 的工作区里用 manage_skill 指定目录，或整包内联上传）
- `references/` — 参考资料，不会自动加载，需要时去读
  - `seedance2-storyboard/` — 下载的 Seedance2 分镜工作流：可套用的提示词、宫斗短剧和燕青打擂台的分镜 / 剧本示例，外加一个未启用的 `seedance-storyboard-generator` skill。写 Seedance 分镜时可以翻
- `character-sheets/` — 每个角色一个子目录：`prompt.md`、`reference.*`、生成结果
- `docs/specs/` — skill 的设计文档
- `shorts/` — 短片项目，每部一个子目录：`README.md`（要做什么 + 资料索引）、`资料/`（原始素材副本）、分镜稿 / 场景稿按版本号迭代

## 约定

- 角色设计（juese-sheji）时：用户本人有服装分类（绅装 / 工装 / 国潮，美式复古 / 阿美咔叽），可以借这套词汇，但角色不是用户本人，按角色逻辑来。
- 风格库同步：用户在主库改了风格页后，在 `.claude/skills/juese-sheji` 下跑 `python3 scripts/sync-styles.py ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/马自立/审美/风格`。
- juese-sheji 有独立的公开仓库（交付给别人用的版本），本地这份是正本，改完在仓库目录跑 `./sync.sh`，见下面「仓库」。
- 生成内容按任务类型分目录存放，不要散落在根目录。
- 同一角色的迭代放在同一目录下，用版本号区分。

## 仓库

- `~/claude/ai-character-design-skill` → github.com/MatsuriMW/ai-character-design-skill：juese-sheji 的独立交付版（README、install.sh、MIT、Release 里有 claude.ai 用的 zip）。改完本地 skill 在那个目录跑 `./sync.sh "说明"`；sync.sh 会顺手用 `package.py` 重新打 `dist/juese-sheji.zip`（别用 macOS 的 zip，中文文件名会乱码）；发新版本 `gh release create vX.Y.Z dist/juese-sheji.zip`，或者给现有版本换附件 `gh release upload vX.Y --clobber dist/juese-sheji.zip`
- `~/claude/aigc-skills-and-agents` → github.com/MatsuriMW/aigc-skills-and-agents：AIGC skill 合集（juese-sheji + character-sheet），`./sync.sh`
