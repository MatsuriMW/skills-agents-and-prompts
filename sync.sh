#!/bin/zsh
# 把散落在本机各处的自制 skill / agent / 提示词同步进这个仓库，然后提交推送。
# 只复制源码和提示词；虚拟环境、模型、索引、.env、生成的成品都不进仓库。
# 文章稿风格提示词的第一部分就是 claude.ai Project「文章稿」的 instructions，正本在主库，改了要手动贴到 claude.ai。
# 用法：./sync.sh [提交说明]
set -e
R="${0:A:h}"
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立"
SS="$HOME/.config/skillshare/skills"   # skill 的正本：skillshare 源，这个仓库只从那里单向导出
EX=(--exclude .DS_Store --exclude __pycache__ --exclude .cache --exclude '*.pyc')
sync_dir() { mkdir -p "$2"; rsync -a --delete $EX "${@:3}" "$1/" "$2/"; }

# 在 skillshare 源里按名字找 skill，不管它放在哪个分组
ss_skill() {
  local d=("$SS"/$1(/N) "$SS"/*/$1(/N))
  [[ -n "$d[1]" ]] || { echo "skillshare 源里找不到 skill：$1" >&2; return 1 }
  print -r -- "$d[1]"
}

# 准入标准：这个仓库只放「我自己做的，或者我改动过的」通用 skill、agent 和提示词。
# - 原样下载的 skill 不进这里，只留在 skillshare 源（私有库 skillshare-source）。
# - AIGC 相关的（古典式配图、角色设定板、aigc 工作区）放 aigc-skills-and-agents，不放这里。
# - 单独建了仓库的 skill 不再留副本，README 里留一行链接。
# 所以下面这个名单就是策展本身：加进来 = 声明「这是我的作品 / 我改过它」。

# skills
for s in wenzhanggao koubo-writer vault-ask wardrobe-intake human-writing chrome-tabgroup-to-obsidian winston-how-to-speak; do
  src=$(ss_skill $s) || exit 1
  sync_dir "$src" "$R/skills/$s"
done

# agents
mkdir -p "$R/agents/writing-agent"
cp "$HOME/Documents/Obsidian Vault/CLAUDE.md" "$R/agents/writing-agent/CLAUDE.md"

mkdir -p "$R/agents/eagle-aesthetic"
cp "$HOME"/claude/eagle-aesthetic/*.py "$R/agents/eagle-aesthetic/"

# ~/Documents/agents/自己写的/ 里的 agent（README.md、.env.example 是仓库里手写的，不覆盖）
MINE="$HOME/Documents/agents/自己写的"
NOPE=(--exclude README.md --exclude .env.example --exclude .env --exclude venv --exclude .venv --exclude .claude --exclude '*.html' --exclude .rag_state.json --exclude docs)
sync_dir "$MINE/invest-agent" "$R/agents/invest-agent" $NOPE
sync_dir "$MINE/openai-rag" "$R/agents/openai-rag" $NOPE

# prompts：主库「写作与创作」里的风格提示词（文章稿是总章，口播稿是口播增量，文白交杂是可选的一层）
for f in 文章稿风格提示词 口播稿风格提示词 文白交杂风格提示词; do cp "$VAULT/写作与创作/$f.md" "$R/prompts/$f.md"; done

cd "$R"
git add -A
if git diff --cached --quiet; then echo "没有变化"; exit 0; fi
git commit -q -m "${1:-同步 skills / agents / prompts}"
git remote get-url origin >/dev/null 2>&1 && git push -q
git log --oneline -1
