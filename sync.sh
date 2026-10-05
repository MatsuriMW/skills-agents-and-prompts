#!/bin/zsh
# 把散落在本机各处的自制 skill / agent / 提示词同步进这个仓库，然后提交推送。
# 只复制源码和提示词；虚拟环境、模型、索引、.env、生成的成品都不进仓库。
# prompts/claude-project-*.md 存的是 claude.ai 云端 Project 的 instructions，本机没有副本，要手动更新。
# 用法：./sync.sh [提交说明]
set -e
R="${0:A:h}"
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立"
SYNCED=("$HOME"/.claude/skills/synced/*(/N[1]))
EX=(--exclude .DS_Store --exclude __pycache__ --exclude .cache --exclude '*.pyc')
sync_dir() { mkdir -p "$2"; rsync -a --delete $EX "${@:3}" "$1/" "$2/"; }

# skills：用户级（~/.claude/skills）
for s in koubo-writer vault-ask wardrobe-intake; do sync_dir "$HOME/.claude/skills/$s" "$R/skills/$s"; done
# skills：在 claude.ai 上建的，桌面端同步下来的副本
sync_dir "$SYNCED/gudianshi-skill" "$R/skills/gudianshi-skill"

# agents
mkdir -p "$R/agents/writing-agent"
cp "$HOME/Documents/Obsidian Vault/CLAUDE.md" "$R/agents/writing-agent/CLAUDE.md"

mkdir -p "$R/agents/aigc-workspace"
cp "$HOME/claude/aigc/CLAUDE.md" "$R/agents/aigc-workspace/CLAUDE.md"
sync_dir "$HOME/claude/aigc/.claude/skills" "$R/agents/aigc-workspace/skills"
sync_dir "$HOME/claude/aigc/references" "$R/agents/aigc-workspace/references"

mkdir -p "$R/agents/eagle-aesthetic"
cp "$HOME"/claude/eagle-aesthetic/*.py "$R/agents/eagle-aesthetic/"

# ~/Documents/agents/自己写的/ 里的 agent（README.md、.env.example 是仓库里手写的，不覆盖）
MINE="$HOME/Documents/agents/自己写的"
NOPE=(--exclude README.md --exclude .env.example --exclude .env --exclude venv --exclude .venv --exclude .claude --exclude '*.html' --exclude .rag_state.json --exclude docs)
sync_dir "$MINE/invest-agent" "$R/agents/invest-agent" $NOPE
sync_dir "$MINE/openai-rag" "$R/agents/openai-rag" $NOPE

# prompts：主库「写作与创作」里的风格提示词
for f in 口播稿风格提示词 书面语风格提示词 文稿风格提示词; do cp "$VAULT/写作与创作/$f.md" "$R/prompts/$f.md"; done

cd "$R"
git add -A
if git diff --cached --quiet; then echo "没有变化"; exit 0; fi
git commit -q -m "${1:-同步 skills / agents / prompts}"
git remote get-url origin >/dev/null 2>&1 && git push -q
git log --oneline -1
