"""在「海报排版」索引里找图：一句话、一张图、或某个已有条目的相似图。

用法:
  .venv/bin/python search.py "大面积留白、只有一行小字的海报"
  .venv/bin/python search.py --image ~/Desktop/ref.jpg
  .venv/bin/python search.py --like <Eagle条目ID>
可选: --style 日式   只在风格路径含该词的图里找
      -k 20          返回数量
      --sheet        在 reports/ 下生成缩略图拼版
      --open N       在 Eagle 里打开前 N 张
      --json         输出 JSON，供 Agent 调用
"""
import argparse
import json
import re
import subprocess
import time

import numpy as np
from PIL import Image, ImageDraw

from common import REPORT_DIR, embed_images, embed_texts, load_index, load_model

Image.MAX_IMAGE_PIXELS = None


def contact_sheet(rows, out_path, cols=5, cell=320):
    n = len(rows)
    lines = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, lines * (cell + 22)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, r in enumerate(rows):
        x, y = (i % cols) * cell, (i // cols) * (cell + 22)
        try:
            im = Image.open(r["path"])
            im.seek(0)
            im = im.convert("RGB")
            im.thumbnail((cell - 8, cell - 8))
            sheet.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        except Exception:
            pass
        draw.text((x + 6, y + cell + 4), f"#{i + 1}  {r['score']:.3f}", fill="black")
    sheet.save(out_path, quality=88)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--image")
    ap.add_argument("--like")
    ap.add_argument("--style")
    ap.add_argument("-k", type=int, default=15)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--open", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    meta, emb = load_index()
    if a.like:
        idx = next(i for i, m in enumerate(meta) if m["id"] == a.like)
        q = emb[idx]
    else:
        model, proc, device = load_model()
        if a.image:
            im = Image.open(a.image).convert("RGB")
            q = embed_images(model, proc, device, [im])[0]
        elif a.query:
            q = embed_texts(model, proc, device, [a.query])[0]
        else:
            ap.error("需要一句话、--image 或 --like")

    scores = emb @ q
    order = np.argsort(-scores)
    rows = []
    for i in order:
        m = meta[i]
        if a.like and m["id"] == a.like:
            continue
        if a.style and not any(a.style in s for s in m["styles"]):
            continue
        rows.append({**m, "score": float(scores[i])})
        if len(rows) >= a.k:
            break

    sheet = None
    if a.sheet:
        REPORT_DIR.mkdir(exist_ok=True)
        tag = re.sub(r"[^\w一-鿿]+", "_", a.query or a.like or "image")[:30]
        sheet = str(contact_sheet(rows, REPORT_DIR / f"search_{tag}_{int(time.time())}.jpg"))

    if a.json:
        print(json.dumps({"results": rows, "sheet": sheet}, ensure_ascii=False, indent=1))
    else:
        for n, r in enumerate(rows, 1):
            print(f"{n:>2}. {r['score']:.3f}  [{' | '.join(r['styles'])}]  {r['name']}.{r['ext']}  eagle://item/{r['id']}")
        if sheet:
            print("拼版:", sheet)
    for r in rows[: a.open]:
        subprocess.run(["open", f"eagle://item/{r['id']}"])


if __name__ == "__main__":
    main()
