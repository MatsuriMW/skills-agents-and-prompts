# Seedance2 Storyboard Generator（参考资料）

2026-10-06 从下载的 `Seedance2-Storyboard-Generator-main` 仓库挪过来的，原目录已删。作者和仓库地址原项目里没写。

原项目的流程：剧本（四幕起承转合）→ 角色 C01 / 场景 S01 / 道具 P01 编号的生图提示词 → Nano Banana 出素材 → Seedance 2.0 按 0-3s / 3-6s … 时间轴写分镜 → 用视频延长把各集接起来。

| 文件 | 是什么 |
|---|---|
| `docs/3组可套用提示词.md` | 三组可以直接套的 Seedance 提示词 |
| `docs/宫斗短剧效果.md` | 宫斗短剧的分镜示例 |
| `docs/燕青打擂台_剧本.md` | 一个完整的剧本示例 |
| `docs/剧本和分镜.md`、`docs/流程.md` | 原项目的流程说明 |
| `docs/structured-prompt.md` | Seedance 2.0 结构化提示词手册（和 `skill/references/seedance-manual.md` 是同一份） |
| `skill/` | 原项目带的 `seedance-storyboard-generator` skill，**没有启用**。想用的话把这个目录复制到 `.claude/skills/seedance-storyboard-generator/`，注意它和 `video` skill 的触发场景重叠 |
| `原项目*.md` | 原项目的 README、CLAUDE.md、项目说明 |
