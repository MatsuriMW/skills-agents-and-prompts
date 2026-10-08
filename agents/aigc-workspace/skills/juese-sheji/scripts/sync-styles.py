#!/usr/bin/env python3
"""从 Obsidian 主库「马自立」的 审美/风格/*.md（type: 审美风格）生成 references/styles/服装风格.md。

主库是正本：在 Obsidian 里加风格页、改单品、写「我的笔记」，跑一次这个脚本就同步进 skill。
用法：python3 scripts/sync-styles.py [风格目录]
"""
import json
import os
import pathlib
import re
import sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = pathlib.Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立/审美/风格"
OUT = SKILL / "references/styles/服装风格.md"


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None
    fm_raw, body = m.groups()
    fm = {}
    for line in fm_raw.split("\n"):
        mm = re.match(r"^([^\s:#][^:]*):\s*(.*)$", line)
        if not mm:
            continue
        k, v = mm.group(1).strip(), mm.group(2).strip()
        if v.startswith("["):
            try:
                v = json.loads(v)
            except ValueError:
                v = [x.strip().strip('"') for x in v.strip("[]").split(",") if x.strip()]
        else:
            v = v.strip('"')
        fm[k] = v
    if fm.get("type") != "审美风格":
        return None
    quote = next((l[2:].strip() for l in body.split("\n") if l.startswith("> ")), "")
    sub = re.search(r"^## 细分\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    subs = [l.strip()[2:] for l in sub.group(1).split("\n") if l.strip().startswith("- ")] if sub else []
    notes = re.search(r"^## 我的笔记\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    note_lines = [l for l in (notes.group(1).split("\n") if notes else []) if l.strip() not in ("", "-")]
    return dict(name=path.stem.replace("（风格）", ""), fm=fm, quote=quote, subs=subs, notes=note_lines)


def as_list(v):
    return v if isinstance(v, list) else ([v] if v else [])


def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    styles = [s for s in (parse(p) for p in sorted(src.glob("*.md"))) if s]
    styles.sort(key=lambda s: (s["fm"].get("类别", ""), int(s["fm"].get("排序") or 999), s["name"]))
    out = [
        "# 服装风格",
        "",
        f"由 `scripts/sync-styles.py` 从主库「马自立」的 `审美/风格/` 生成（{len(styles)} 个风格），**不要手改这个文件**：改主库的风格页再跑脚本。",
        "",
        "用法见 `索引.md`。落到人物身上时，从「经典单品」里挑 3–5 件，按 `../dimensions/04-服装.md` 往下切到款式、版型、面料、穿法；配色直接用 HEX；「要当心」那一条通常就是这个人的破绽或者可以反转的地方。",
        "品牌只作风格参照、帮你想起具体的样子，锁定段里不写品牌和 logo，换成款式描述。",
        "",
        "| 风格 | 关键词 | 类别 · 层级 |",
        "|---|---|---|",
    ]
    for s in styles:
        fm = s["fm"]
        out.append(f"| [{s['name']}](#{s['name']}) | {'、'.join(as_list(fm.get('关键词')))} | {fm.get('类别', '')} · {fm.get('层级', '')} |")
    for s in styles:
        fm = s["fm"]
        out += ["", f"## {s['name']}", ""]
        if s["quote"]:
            out += [f"> {s['quote']}", ""]
        if as_list(fm.get("aliases")):
            out.append(f"- **别名**：{'、'.join(as_list(fm.get('aliases')))}")
        out.append(f"- **关键词**：{'、'.join(as_list(fm.get('关键词')))}")
        out.append(f"- **经典单品**：{'、'.join(as_list(fm.get('经典单品')))}")
        if fm.get("入门"):
            out.append(f"- **最小组合**：{fm['入门']}")
        if as_list(fm.get("配色")):
            out.append(f"- **配色**：{' '.join(as_list(fm.get('配色')))}")
        if fm.get("风险"):
            out.append(f"- **要当心**：{fm['风险']}")
        brands = as_list(fm.get("品牌")) + as_list(fm.get("国内品牌"))
        if brands:
            out.append(f"- **参照品牌**：{'、'.join(brands)}")
        if s["subs"]:
            out.append("- **细分**：")
            out += [f"  - {x}" for x in s["subs"]]
        if s["notes"]:
            out.append("- **马自立的笔记**：")
            out += ["  " + l if l.startswith("-") else "  - " + l.strip() for l in s["notes"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已生成 {OUT.relative_to(SKILL)}：{len(styles)} 个风格")


if __name__ == "__main__":
    main()
