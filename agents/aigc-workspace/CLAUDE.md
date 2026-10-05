# AIGC 工作区

AI 生成内容（生图 / 生视频 / 角色设定）相关任务的工作目录。

## 目录

- `.claude/skills/` — 本工作区专属 skill，只在 aigc 目录内启动 Claude Code 时加载
  - `character-sheet/` — 角色设定板（Character Sheet）prompt 制作
  - `cinematic-director/` — 分镜 / 导演流程（第三方 wuwangzhang1216/DirectorSKILL，MIT）。本地加了 `director_styles/21_johnnie_to.md` 和 `references/visual-vocabulary-zh.md`，更新上游时注意保留
  - `video/`、`image/` — 按模型写生视频 / 生图提示词（第三方 smixs/visual-skills，CC-BY-4.0）
  - 各第三方 skill 的来源和 commit 记在各自目录的 `.source`
- `character-sheets/` — 每个角色一个子目录：`prompt.md`、`reference.*`、生成结果
- `shorts/` — 短片项目，每部一个子目录：`README.md`（要做什么 + 资料索引）、`资料/`（原始素材副本）、分镜稿 / 场景稿按版本号迭代

## 约定

- 生成内容按任务类型分目录存放，不要散落在根目录。
- 同一角色的迭代放在同一目录下，用版本号区分。
