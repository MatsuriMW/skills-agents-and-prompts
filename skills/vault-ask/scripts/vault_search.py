#!/usr/bin/env python3
"""Search the 马自立 Obsidian vault and return citable hits.

Journals (日记/) return only the matching list block: its ancestor chain
(first line of each parent) plus the block and its children. Other notes
return frontmatter summary and matching lines with context.

Examples:
  vault_search.py 拖延 不想动 启动困难
  vault_search.py 心流 --scope journal --since 2024-01-01
  vault_search.py --backlinks 心流
  vault_search.py 周期 --scope notes --context 3
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import date

VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立")
JOURNAL_DIR = "日记"
EXCLUDE = [".obsidian", ".trash", "assets", "Templates", "scripts", "问答", "Wiki"]
DATE_RE = re.compile(r"(\d{4})[_-](\d{1,2})[_-](\d{1,2})")
ITEM_RE = re.compile(r"^(\t*)- ")
FLASHCARD_ID_RE = re.compile(r"^\s*\^q-\w+\s*$")
BLOCK_ID_RE = re.compile(r"\s\^([\w-]+)\s*$")


def journal_date(path):
    m = DATE_RE.search(os.path.basename(path))
    if not m:
        return None
    try:
        return date(*map(int, m.groups()))
    except ValueError:
        return None


def build_pattern(terms, backlinks):
    parts = []
    for t in terms:
        e = re.escape(t)
        # [[t]] / [[t|x]] / [[t#x]] / #t
        parts.append(rf"\[\[{e}(\|[^\]]*)?(#[^\]]*)?\]\]|#{e}\b" if backlinks else e)
    return "|".join(f"(?:{p})" for p in parts)


def rg_files(pattern, scope):
    cmd = ["rg", "-l", "-i", "--pcre2", "-g", "*.md"]
    for d in EXCLUDE:
        cmd += ["-g", f"!{d}/**"]
    if scope == "journal":
        cmd += ["-e", pattern, JOURNAL_DIR]
    elif scope == "notes":
        cmd += ["-g", f"!{JOURNAL_DIR}/**", "-e", pattern, "."]
    else:
        cmd += ["-e", pattern, "."]
    out = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True).stdout
    return [p[2:] if p.startswith("./") else p for p in out.splitlines()]


def rg_filenames(terms):
    out = subprocess.run(["rg", "--files", "-g", "*.md"] +
                         sum([["-g", f"!{d}/**"] for d in EXCLUDE], []),
                         cwd=VAULT, capture_output=True, text=True).stdout
    low = [t.lower() for t in terms]
    return [p for p in out.splitlines()
            if any(t in os.path.basename(p).lower() for t in low)]


def split_frontmatter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[1:i], i + 1
    return [], 0


def parse_items(lines, start):
    """Return list of (depth, first_line_idx, last_line_idx)."""
    items = []
    for i in range(start, len(lines)):
        line = lines[i]
        if FLASHCARD_ID_RE.match(line):
            continue
        m = ITEM_RE.match(line)
        if m:
            items.append([len(m.group(1)), i, i])
        elif line.strip():
            if items:
                items[-1][2] = i
            else:
                items.append([0, i, i])
    return items


def ancestors(items, idx):
    """Indices of enclosing items, outermost first."""
    out, d = [], items[idx][0]
    for j in range(idx - 1, -1, -1):
        if items[j][0] < d:
            out.append(j)
            d = items[j][0]
            if d == 0:
                break
    return out[::-1]


def subtree_end(items, idx):
    end = items[idx][2]
    for j in range(idx + 1, len(items)):
        if items[j][0] <= items[idx][0]:
            break
        end = items[j][2]
    return end


def journal_hits(path, rx):
    with open(os.path.join(VAULT, path), encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    _, body = split_frontmatter(lines)
    items = parse_items(lines, body)
    blocks, covered = [], -1
    for idx, (depth, a, b) in enumerate(items):
        if a <= covered:
            continue
        if not any(rx.search(lines[k]) for k in range(a, b + 1)):
            continue
        anc_idx = ancestors(items, idx)
        end = subtree_end(items, idx)
        # A short leaf like "《[[心流]]》给出了终极答案" carries its substance in
        # sibling blocks, so widen to the parent's subtree.
        own = "".join(lines[a:b + 1]).strip()
        if end == b and anc_idx and len(own) < 80:
            idx = anc_idx.pop()
            a, end = items[idx][1], subtree_end(items, idx)
        if blocks and a <= covered:
            continue
        anc = [lines[items[j][1]] for j in anc_idx]
        covered = end
        text = [l for l in lines[a:end + 1] if not FLASHCARD_ID_RE.match(l)]
        ids = [m.group(1) for l in lines[a:items[idx][2] + 1]
               if (m := BLOCK_ID_RE.search(l))]
        blocks.append((anc, text, ids))
    return blocks


def note_hits(path, rx, ctx):
    with open(os.path.join(VAULT, path), encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    fm, body = split_frontmatter(lines)
    meta = [l for l in fm if re.match(r"^(type|def|aliases|tags):", l)]
    hits = [i for i in range(body, len(lines)) if rx.search(lines[i])]
    fm_hit = any(rx.search(l) for l in fm)
    snippets, last = [], -1
    for i in hits:
        a, b = max(body, i - ctx), min(len(lines) - 1, i + ctx)
        if a <= last:
            snippets[-1][1] = b
        else:
            snippets.append([a, b])
        last = b
    seen, out = set(), []
    for a, b in snippets:
        key = "\n".join(lines[a:b + 1])
        if key not in seen:
            seen.add(key)
            out.append(lines[a:b + 1])
    return meta, fm_hit, len(hits), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--scope", choices=["all", "journal", "notes"], default="all")
    ap.add_argument("--backlinks", action="store_true",
                    help="match [[term]] links and #term tags instead of plain text")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--max-notes", type=int, default=40)
    ap.add_argument("--max-journal", type=int, default=80)
    ap.add_argument("--max-snippets", type=int, default=3)
    a = ap.parse_args()

    pattern = build_pattern(a.terms, a.backlinks)
    rx = re.compile(pattern, re.I)
    since = date.fromisoformat(a.since) if a.since else None
    until = date.fromisoformat(a.until) if a.until else None

    files = rg_files(pattern, a.scope)
    journals = sorted((p for p in files if p.startswith(JOURNAL_DIR + "/")),
                      key=lambda p: journal_date(p) or date.min)
    notes = [p for p in files if not p.startswith(JOURNAL_DIR + "/")]
    name_hits = [] if a.backlinks or a.scope == "journal" else \
        [p for p in rg_filenames(a.terms) if not p.startswith(JOURNAL_DIR + "/")]

    if since or until:
        journals = [p for p in journals if (d := journal_date(p)) and
                    (not since or d >= since) and (not until or d <= until)]

    print(f"# terms: {' | '.join(a.terms)}  (backlinks={a.backlinks}, scope={a.scope})")
    print(f"# notes: {len(notes)}  journals: {len(journals)}  filename matches: {len(name_hits)}\n")

    if name_hits:
        print("## 文件名命中")
        for p in name_hits:
            print(f"- [[{os.path.splitext(os.path.basename(p))[0]}]]  ({p})")
        print()

    if notes and a.scope != "journal":
        print("## 笔记命中（按命中次数）")
        rows = [(p, *note_hits(p, rx, a.context)) for p in notes]
        rows.sort(key=lambda r: -r[3])
        for p, meta, fm_hit, n, snips in rows[:a.max_notes]:
            name = os.path.splitext(os.path.basename(p))[0]
            print(f"### [[{name}]]  ({p}, 正文命中 {n}{', frontmatter 命中' if fm_hit else ''})")
            for m in meta:
                print(f"  {m}")
            for s in snips[:a.max_snippets]:
                print("  ```")
                for l in s:
                    print("  " + l)
                print("  ```")
        if len(rows) > a.max_notes:
            print(f"\n… 还有 {len(rows) - a.max_notes} 篇笔记未显示："
                  + ", ".join(os.path.basename(r[0]) for r in rows[a.max_notes:]))
        print()

    if journals and a.scope != "notes":
        print("## 日记块命中（按日期）")
        shown = 0
        for p in journals:
            if shown >= a.max_journal:
                print(f"\n… 还有 {len(journals) - shown} 篇日记未显示，用 --since/--until 缩小范围")
                break
            blocks = journal_hits(p, rx)
            if not blocks:
                continue
            name = os.path.splitext(os.path.basename(p))[0]
            for anc, text, ids in blocks:
                ref = f"[[{name}#^{ids[0]}]]" if ids else f"[[{name}]]"
                print(f"### {ref}")
                for l in anc:
                    print("  (上级) " + l.strip()[:120])
                for l in text:
                    print("  " + l)
            shown += 1


if __name__ == "__main__":
    sys.exit(main())
