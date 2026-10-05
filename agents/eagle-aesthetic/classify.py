"""用已分好风格的图做样本，给「原始文件」里的图推荐风格。只输出清单，不写回 Eagle。

用法: .venv/bin/python classify.py
输出: reports/classify.csv        每张未分类图的推荐风格、置信度、次选
      reports/classify_summary.md 各风格的自测准确率与推荐数量
      reports/sheets/             每个风格的推荐样例拼版、候选新风格拼版
"""
import collections
import csv

import numpy as np
from sklearn.cluster import KMeans

from common import REPORT_DIR, load_index
from search import contact_sheet

UNSORTED = "北欧设计/原始文件"
K = 15
MIN_SAMPLES = 15  # 样本太少的风格不参与自动推荐
CONF_HIGH, CONF_LOW = 0.6, 0.35


def knn_vote(sim, labels, k=K):
    """sim: (n_query, n_labeled) 余弦相似度。返回每行的 [(风格, 得票占比), ...] 降序。"""
    out = []
    top = np.argsort(-sim, axis=1)[:, :k]
    for row, idx in zip(sim, top):
        votes = collections.Counter()
        for j in idx:
            votes[labels[j]] += max(row[j], 0)
        total = sum(votes.values()) or 1
        out.append([(s, v / total) for s, v in votes.most_common()])
    return out


def main():
    meta, emb = load_index()
    lab_idx, lab_style, unl_idx = [], [], []
    counts = collections.Counter(s for m in meta for s in m["styles"] if s != UNSORTED)
    usable = {s for s, c in counts.items() if c >= MIN_SAMPLES}
    for i, m in enumerate(meta):
        styles = [s for s in m["styles"] if s != UNSORTED]
        if styles:
            if styles[0] in usable:
                lab_idx.append(i)
                lab_style.append(styles[0])
        elif UNSORTED in m["styles"]:
            unl_idx.append(i)
    L, U = emb[lab_idx], emb[unl_idx]
    print(f"样本 {len(lab_idx)} 张 / {len(usable)} 个风格；待分类 {len(unl_idx)} 张")

    # 自测：每张样本图拿掉自己，看能否被分回原风格
    sim = L @ L.T
    np.fill_diagonal(sim, -1)
    pred = knn_vote(sim, lab_style)
    hit, tot, confused = collections.Counter(), collections.Counter(), collections.Counter()
    for truth, p in zip(lab_style, pred):
        tot[truth] += 1
        if p[0][0] == truth:
            hit[truth] += 1
        else:
            confused[(truth, p[0][0])] += 1
    acc = sum(hit.values()) / len(lab_style)

    # 给未分类图推荐
    votes = knn_vote(U @ L.T, lab_style)
    REPORT_DIR.mkdir(exist_ok=True)
    sheets = REPORT_DIR / "sheets"
    sheets.mkdir(exist_ok=True)
    rows, by_style, low = [], collections.defaultdict(list), []
    for i, v in zip(unl_idx, votes):
        m = meta[i]
        s1, c1 = v[0]
        s2, c2 = v[1] if len(v) > 1 else ("", 0)
        level = "高" if c1 >= CONF_HIGH else "中" if c1 >= CONF_LOW else "低"
        rows.append([m["id"], m["name"], s1, f"{c1:.2f}", level, s2, f"{c2:.2f}", f"eagle://item/{m['id']}"])
        if level == "低":
            low.append(i)
        else:
            by_style[s1].append({**m, "score": c1})
    with open(REPORT_DIR / "classify.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "文件名", "推荐风格", "置信度", "档位", "次选风格", "次选置信度", "链接"])
        w.writerows(rows)

    for s, items in by_style.items():
        items.sort(key=lambda r: -r["score"])
        contact_sheet(items[:25], sheets / f"推荐_{s.replace('/', '-')}.jpg")

    # 对不上现有风格的图单独聚类，看有没有未命名的新风格
    clusters = []
    if len(low) >= 40:
        n = min(12, len(low) // 20)
        km = KMeans(n_clusters=n, n_init=10, random_state=0).fit(emb[low])
        for c in range(n):
            members = [low[j] for j in np.where(km.labels_ == c)[0]]
            d = emb[members] @ km.cluster_centers_[c]
            picks = [{**meta[members[j]], "score": float(d[j])} for j in np.argsort(-d)[:25]]
            contact_sheet(picks, sheets / f"候选新风格_{c + 1:02d}_{len(members)}张.jpg")
            clusters.append((c + 1, len(members)))

    level_count = collections.Counter(r[4] for r in rows)
    md = [
        "# 风格分类结果（未写回 Eagle）",
        "",
        f"- 样本：{len(lab_idx)} 张，{len(usable)} 个风格（少于 {MIN_SAMPLES} 张的风格未参与）",
        f"- 待分类：{len(unl_idx)} 张；高置信 {level_count['高']}，中 {level_count['中']}，低 {level_count['低']}",
        f"- 自测总体准确率：{acc:.1%}",
        "",
        "| 风格 | 样本数 | 自测准确率 | 推荐归入（高+中） |",
        "|---|---|---|---|",
    ]
    for s in sorted(usable, key=lambda s: -tot[s]):
        md.append(f"| {s} | {tot[s]} | {hit[s] / tot[s]:.0%} | {len(by_style.get(s, []))} |")
    md += ["", "## 最容易混淆的风格", "", "| 原风格 | 被分到 | 张数 |", "|---|---|---|"]
    for (a, b), n in confused.most_common(12):
        md.append(f"| {a} | {b} | {n} |")
    if clusters:
        md += ["", "## 候选新风格（低置信图聚类）", ""]
        md += [f"- 第 {c} 组：{n} 张" for c, n in clusters]
    skipped = sorted((s, c) for s, c in counts.items() if s not in usable)
    if skipped:
        md += ["", "## 样本太少未参与的风格", ""] + [f"- {s}：{c} 张" for s, c in skipped]
    (REPORT_DIR / "classify_summary.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
