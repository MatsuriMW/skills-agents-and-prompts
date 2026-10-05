#!/usr/bin/env python3
"""按意思检索「马自立」库里的块（日记的每个顶层列表项、笔记的段落）。

和 Obsidian 里「第二大脑」插件的写作模式共用一份向量缓存
（~/.cache/second-brain/vectors/embeddinggemma-768/），所以一般不用重新算；
缓存里没有的块会现算并追加进去。需要本机 Ollama 开着，且有 embeddinggemma 模型。

用法：
  sem_search.py "一段话或一个想法" ["第二个说法" ...]   # 多个说法会分别检索再合并
  sem_search.py "……" --top 20 --scope journal|notes|all --since 2024-01-01
输出：每条一行出处（路径:行号）+ 原文（截断），按相关度排序。
"""
import argparse, hashlib, json, os, re, sys, urllib.request
import numpy as np

VAULT = os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立")
MODEL, DIMS = "embeddinggemma", 768
CACHE = os.path.expanduser(f"~/.cache/second-brain/vectors/{MODEL}-{DIMS}")
OLLAMA = "http://127.0.0.1:11434/api/embed"
Q_PREFIX, D_PREFIX = "task: search result | query: ", "title: none | text: "
EXCLUDE = ("Templates/", "scripts/", "Bases/", "选题/_采访/", "Wiki/")
EXCLUDE_FILES = {"计划与总结/库周报.md"}
PRIVATE = re.compile(r"\[\[(?:[^\]|]*/)?(?:宝a|宝)(?:[|#\]])")   # 这些块不拿来当素材
JOURNAL = re.compile(r"^(\d{4})[_-](\d{1,2})[_-](\d{1,2})$")
LIST = re.compile(r"^([-*+]|\d+[.)])\s")


def blocks_of(text, base):
    """和插件里 fsBlocks 一样的切法（切法一致，内容哈希才对得上缓存）。"""
    res = []
    L = text.split("\n")
    i, fm = 0, ""
    if L and L[0] == "---":
        e = 1
        while e < len(L) and L[e] != "---":
            e += 1
        fm = "\n".join(L[1:e]); i = e + 1
    is_journal = bool(JOURNAL.match(base))

    def push(line, s):
        t = s.strip()
        if len(re.sub(r"\s", "", t)) < 8 or PRIVATE.search(t):
            return
        res.append((line, t))

    if not is_journal:
        m = re.search(r'^def:\s*"?(.*?)"?\s*$', fm, re.M)
        push(0, f"{base} {m.group(1) if m else ''}")
    cur = para = None
    cur_line = para_line = 0
    in_code = False

    def flush():
        nonlocal cur, para
        if cur is not None:
            push(cur_line, cur); cur = None
        if para is not None:
            if not is_journal:
                push(para_line, para)
            para = None

    while i < len(L):
        l = L[i]
        if re.match(r"^\s*(```|~~~)", l):
            in_code = not in_code; flush()
        elif in_code:
            pass
        elif LIST.match(l):
            flush(); cur, cur_line = l, i
        elif cur is not None and l.strip() and re.match(r"^\s", l):
            cur += "\n" + l
        elif not l.strip() or re.match(r"^#{1,6}\s", l) or l.startswith("|"):
            flush()
        else:
            if cur is not None:
                flush()
            if para is None:
                para, para_line = l, i
            else:
                para += "\n" + l
        i += 1
    flush()
    return res


def all_blocks(scope, since):
    out = []
    for dp, dn, fn in os.walk(VAULT):
        dn[:] = [d for d in dn if not d.startswith(".")]
        for f in fn:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, VAULT)
            if rel.startswith(EXCLUDE) or rel in EXCLUDE_FILES:
                continue
            base = f[:-3]
            jm = JOURNAL.match(base)
            if scope == "journal" and not jm or scope == "notes" and jm:
                continue
            if since and jm and "%s-%02d-%02d" % (jm.group(1), int(jm.group(2)), int(jm.group(3))) < since:
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except Exception:
                continue
            for line, t in blocks_of(text, base):
                t = t[:1200]
                out.append((rel, line, t, hashlib.sha1(t.encode("utf-8")).hexdigest()[:20]))
    return out


def embed(texts, prefix):
    req = urllib.request.Request(OLLAMA, data=json.dumps({"model": MODEL, "input": [prefix + t for t in texts], "dimensions": DIMS, "truncate": True}).encode(), headers={"Content-Type": "application/json"})
    v = np.array(json.load(urllib.request.urlopen(req, timeout=300))["embeddings"], dtype=np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def load_cache():
    hp, vp = os.path.join(CACHE, "hashes.txt"), os.path.join(CACHE, "vecs.bin")
    if not (os.path.exists(hp) and os.path.exists(vp)):
        return {}, np.zeros((0, DIMS), dtype=np.float32)
    hs = [h for h in open(hp).read().split("\n") if h]
    vecs = np.fromfile(vp, dtype=np.float32)
    n = min(len(hs), len(vecs) // DIMS)
    return {h: i for i, h in enumerate(hs[:n])}, vecs[: n * DIMS].reshape(n, DIMS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--scope", choices=["all", "journal", "notes"], default="all")
    ap.add_argument("--since", help="只看这天之后的日记，YYYY-MM-DD")
    ap.add_argument("--width", type=int, default=260, help="每条原文显示多少字")
    a = ap.parse_args()

    blocks = all_blocks(a.scope, a.since)
    idx, vecs = load_cache()
    missing = {}
    for rel, line, t, h in blocks:
        if h not in idx and h not in missing:
            missing[h] = t
    try:
        if missing:
            print(f"（{len(missing)} 个块还没有向量，现算并写进缓存…）", file=sys.stderr)
            os.makedirs(CACHE, exist_ok=True)
            items = list(missing.items())
            new = []
            for i in range(0, len(items), 32):
                v = embed([t for _, t in items[i:i + 32]], D_PREFIX)
                with open(os.path.join(CACHE, "vecs.bin"), "ab") as f:
                    f.write(v.astype(np.float32).tobytes())
                with open(os.path.join(CACHE, "hashes.txt"), "a") as f:
                    f.write("\n".join(h for h, _ in items[i:i + 32]) + "\n")
                new.append(v)
            base = len(idx)
            for k, (h, _) in enumerate(items):
                idx[h] = base + k
            vecs = np.vstack([vecs] + new)
        q = embed([x[:1200] for x in a.queries], Q_PREFIX)
    except Exception as e:
        sys.exit(f"连不上 Ollama（{e}）。先打开 Ollama，或者改用 vault-ask 的关键词检索。")

    rows = np.array([idx[h] for _, _, _, h in blocks])
    sims = (vecs[rows] @ q.T).max(axis=1)          # 多个说法取最高分
    seen, shown, per_file = set(), 0, {}
    for i in np.argsort(-sims):
        rel, line, t, h = blocks[i]
        key = re.sub(r"\s+", "", t)[:80]
        if key in seen or per_file.get(rel, 0) >= 2:
            continue
        seen.add(key); per_file[rel] = per_file.get(rel, 0) + 1
        one = re.sub(r"\s+", " ", t)
        print(f"[{sims[i]:.2f}] {rel}:{line + 1}\n    {one[:a.width]}{'…' if len(one) > a.width else ''}")
        shown += 1
        if shown >= a.top:
            break


if __name__ == "__main__":
    main()
