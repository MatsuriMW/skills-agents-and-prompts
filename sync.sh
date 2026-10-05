#!/bin/zsh
# 本机各处的自制 skill / agent / 提示词 <-> 这个仓库。
# 只复制源码和提示词；虚拟环境、模型、索引、.env、生成的成品都不进仓库。
# prompts/claude-project-*.md 存的是 claude.ai 云端 Project 的 instructions，本机没有副本，要手动更新。
#
# 用法：
#   ./sync.sh [提交说明]              本机 → 仓库：复制、提交、推送（平时用这个）
#   ./sync.sh --pull [-n] [-y]        仓库 → 本机：拉下仓库里的新提交（比如在网页上让 Claude 改的），写回本机正本
#                                     -n 只列出会改哪些文件，不动手；-y 不再问确认
#   ./sync.sh --pull --base <提交>    第一次用 --pull 时要告诉它：本机现在的样子对应仓库的哪个提交
#
# 怎么防止互相覆盖：.git/sync-local-base 记着「本机现在和仓库的哪个提交一致」。
#   · 本机 → 仓库时，如果仓库已经有本机没写回的新提交，就停下，让你先 --pull，免得用本机的旧文件把新改动盖掉
#   · 仓库 → 本机时，如果本机有还没进仓库的改动，也停下，让你先 ./sync.sh 提交它们（之后 --pull 会用 git 合并两边）
#   · 写回本机前，被覆盖或删除的文件都先备份到 ~/.cache/skills-sync-backup/<时间>/
set -e
R="${0:A:h}"
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立"
SYNCED=("$HOME"/.claude/skills/synced/*(/N[1]))
MINE="$HOME/Documents/agents/自己写的"
EX=(--exclude .DS_Store --exclude __pycache__ --exclude .cache --exclude '*.pyc' --exclude .pytest_cache)
# 自己写的 agent：README.md、.env.example 是仓库里手写的，两个方向都不碰
NOPE=(--exclude README.md --exclude .env.example --exclude .env --exclude venv --exclude .venv --exclude .claude --exclude '*.html' --exclude .rag_state.json --exclude docs)

# 本机路径和仓库路径的对应表。两个方向都用它：$1 是对每一项要做的事
mappings() {
  local s f
  for s in koubo-writer vault-ask wardrobe-intake; do $1 dir "$HOME/.claude/skills/$s" "skills/$s"; done
  # 在 claude.ai 上建的 skill，本机是桌面端同步下来的副本：只往仓库同步，不往回写
  $1 cloud "$SYNCED/gudianshi-skill" "skills/gudianshi-skill"

  $1 file "$HOME/Documents/Obsidian Vault/CLAUDE.md" "agents/writing-agent/CLAUDE.md"
  $1 file "$HOME/claude/aigc/CLAUDE.md" "agents/aigc-workspace/CLAUDE.md"
  $1 dir "$HOME/claude/aigc/.claude/skills" "agents/aigc-workspace/skills"
  $1 dir "$HOME/claude/aigc/references" "agents/aigc-workspace/references"
  # eagle-aesthetic 只同步顶层的 .py（模型、索引、虚拟环境不进仓库；README 是仓库里手写的）
  $1 dir "$HOME/claude/eagle-aesthetic" "agents/eagle-aesthetic" --include '*.py' --exclude '*'
  $1 dir "$MINE/invest-agent" "agents/invest-agent" $NOPE
  $1 dir "$MINE/openai-rag" "agents/openai-rag" $NOPE

  # 主库「写作与创作」里的风格提示词
  for f in 口播稿风格提示词 书面语风格提示词 文稿风格提示词; do $1 file "$VAULT/写作与创作/$f.md" "prompts/$f.md"; done
}

cd "$R"
BASE_FILE="$(git rev-parse --git-dir)/sync-local-base"
has_remote() { git remote get-url origin >/dev/null 2>&1 }
behind() { git rev-list --count HEAD..@{u} 2>/dev/null || echo 0 }
ahead() { git rev-list --count @{u}..HEAD 2>/dev/null || echo 1 }

# ---------- 本机 → 仓库 ----------
to_repo() {
  local kind=$1 src=$2 dst="$R/$3"; shift 3
  if [[ ! -e $src ]]; then echo "跳过（本机没有）：$src"; return; fi
  case $kind in
    file) mkdir -p "${dst:h}"; cp "$src" "$dst" ;;
    *)    mkdir -p "$dst"; rsync -a --delete $EX "$@" "$src/" "$dst/" ;;
  esac
}

push_mode() {
  if [[ ! -f $BASE_FILE ]]; then
    echo "第一次用新版 sync.sh，先记下本机现在对应仓库的哪个提交（这一步不会改本机，除非仓库比本机新）："
    echo "  ./sync.sh --pull --base <上次跑 ./sync.sh 时生成的那个提交> -n    # 先看看"
    echo "确定本机和仓库现在完全一致的话，用 --base HEAD。最近的提交："; git log --oneline -8
    exit 1
  fi
  if [[ $(git rev-parse HEAD) != $(<$BASE_FILE) ]]; then
    echo "仓库里有本机还没写回的新提交（${$(<$BASE_FILE):0:7}..$(git rev-parse --short HEAD)）。"
    echo "直接同步会用本机的旧文件把它们盖掉。先跑 ./sync.sh --pull"
    exit 1
  fi
  mappings to_repo
  git add -A
  if git diff --cached --quiet; then
    echo "没有变化"
  else
    git commit -q -m "${1:-同步 skills / agents / prompts}"
    git log --oneline -1
  fi
  git rev-parse HEAD > "$BASE_FILE"
  has_remote || return 0
  git fetch -q origin
  if (( $(behind) > 0 )); then
    echo "远端有 $(behind) 个新提交（可能是在网页上改的），这次先不推送。"
    echo "跑 ./sync.sh --pull：它会合并两边、写回本机，再推送。"
    exit 1
  fi
  (( $(ahead) == 0 )) || git push -q
}

# ---------- 仓库 → 本机 ----------
# 列出 from → to 之间会变的文件（按内容比，不看修改时间）
changes() {
  local kind=$1 from=$2 to=$3; shift 3
  case $kind in
    file) [[ -f $from ]] && ! cmp -s "$from" "$to" && echo "  改  $to" ;;
    *)    [[ -d $from ]] && rsync -anic --delete $EX "$@" "$from/" "$to/" \
            | grep -E '^(\*deleting|[<>c][fL])' \
            | sed -E "s#^\*deleting +#  删  $to/#; s#^[<>c][fL]\+{9} +#  新  $to/#; s#^[^ ]+ +#  改  $to/#" ;;
  esac
  return 0
}

# 本机相对 base 有没有没进仓库的改动
SNAP=""
local_drift() {
  local kind=$1 src=$2 rel=$3; shift 3
  [[ $kind == cloud || ! -e $src ]] && return
  changes $kind "$src" "$SNAP/$rel" "$@" | sed "s#$SNAP/##"
}

preview() {
  local kind=$1 dst=$2 rel=$3; shift 3
  [[ $kind == cloud ]] && return
  changes $kind "$R/$rel" "$dst" "$@"
}

BACKUP=""
to_local() {
  local kind=$1 dst=$2 rel=$3; shift 3
  [[ $kind == cloud ]] && return
  [[ -e "$R/$rel" ]] || return 0
  case $kind in
    file)
      cmp -s "$R/$rel" "$dst" && return
      if [[ -f $dst ]]; then mkdir -p "$BACKUP/${rel:h}"; cp "$dst" "$BACKUP/$rel"; fi
      mkdir -p "${dst:h}"; cp "$R/$rel" "$dst" ;;
    *)
      mkdir -p "$dst"
      rsync -ac --delete --backup --backup-dir="$BACKUP/$rel" $EX "$@" "$R/$rel/" "$dst/" ;;
  esac
}

pull_mode() {
  local dry=0 yes=0 base=""
  while (( $# )); do
    case $1 in
      -n) dry=1 ;;
      -y) yes=1 ;;
      --base) base=$(git rev-parse --verify "$2^{commit}"); shift ;;
      *) echo "不认识的参数：$1"; exit 2 ;;
    esac
    shift
  done
  [[ -z $base && -f $BASE_FILE ]] && base=$(<$BASE_FILE)
  if [[ -z $base ]]; then
    echo "第一次用 --pull，要先说明本机现在的样子对应仓库的哪个提交："
    echo "  ./sync.sh --pull --base <上次跑 ./sync.sh 时生成的那个提交> -n"
    echo "最近的提交："; git log --oneline -8
    exit 1
  fi
  if [[ -n $(git status --porcelain) ]]; then
    echo "仓库里有没提交的改动，先处理掉再 --pull："; git status --short; exit 1
  fi

  # 1. 本机有没有还没进仓库的改动
  SNAP=$(mktemp -d)
  git archive "$base" | tar -x -C "$SNAP"
  local drift; drift=$(mappings local_drift)
  rm -rf "$SNAP"
  if [[ -n $drift ]]; then
    echo "本机有还没进仓库的改动（和提交 ${base:0:7} 比）："; echo "$drift"
    echo "直接写回会把它们盖掉。先跑 ./sync.sh 把它们提交进仓库，再 --pull（会用 git 合并两边）。"
    exit 1
  fi

  # 2. 拉远端
  if has_remote && git rev-parse @{u} >/dev/null 2>&1; then
    git pull -q --no-rebase || { echo "合并有冲突：解决后 git commit，再跑一次 ./sync.sh --pull"; exit 1; }
  fi

  # 3. 看会改本机哪些文件
  local todo; todo=$(mappings preview | sed "s#$HOME/#~/#")
  if git diff --quiet "$base" HEAD -- skills/gudianshi-skill 2>/dev/null; then :; else
    echo "注意：skills/gudianshi-skill 在仓库里有改动，但它的正本在 claude.ai，不会写回本机，要去 claude.ai 改。"
  fi
  if [[ -z $todo ]]; then
    echo "本机已经是最新的"
    (( dry )) || git rev-parse HEAD > "$BASE_FILE"
  else
    echo "会改本机这些文件："; echo "$todo"
    (( dry )) && { echo "（-n：只看不改）"; exit 0; }
    if (( ! yes )); then
      read -q "?写回本机？[y/N] " || { echo; echo "没动"; exit 1; }
      echo
    fi
    BACKUP="$HOME/.cache/skills-sync-backup/$(date +%Y%m%d-%H%M%S)"
    mappings to_local
    git rev-parse HEAD > "$BASE_FILE"
    echo "写回完成。被覆盖或删除的旧文件备份在 $BACKUP"
  fi
  if has_remote && (( $(ahead) > 0 )); then git push -q && echo "已推送合并结果"; fi
  return 0
}

if [[ $1 == --pull ]]; then shift; pull_mode "$@"; else push_mode "$@"; fi
