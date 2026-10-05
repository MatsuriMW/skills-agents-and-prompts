"""给「海报排版」下的图片建立 SigLIP2 向量索引。增量：已索引的条目不重算。

用法: .venv/bin/python build_index.py [--limit N]
"""
import argparse
import json
import time

import numpy as np
from PIL import Image

from common import EMB_PATH, INDEX_DIR, META_PATH, embed_images, list_items, load_model

BATCH = 16
Image.MAX_IMAGE_PIXELS = None


def open_image(path):
    im = Image.open(path)
    im.seek(0)  # gif 取首帧
    im = im.convert("RGB")
    im.thumbnail((1024, 1024))  # 模型输入只有 384，先缩小省内存
    return im


def save(meta, emb):
    INDEX_DIR.mkdir(exist_ok=True)
    np.save(EMB_PATH, np.asarray(emb, dtype=np.float32))
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 张，用于试跑")
    args = ap.parse_args()

    items = list_items()
    by_id = {it["id"]: it for it in items}
    meta, emb = [], []
    if META_PATH.exists() and EMB_PATH.exists():
        old_meta = json.loads(META_PATH.read_text())
        old_emb = np.load(EMB_PATH)
        for m, e in zip(old_meta, old_emb):
            if m["id"] in by_id:  # Eagle 里已删除的条目顺带剔除
                meta.append(by_id[m["id"]])  # 风格路径以 Eagle 当前状态为准
                emb.append(e)
    done = {m["id"] for m in meta}
    todo = [it for it in items if it["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"共 {len(items)} 张，已索引 {len(done)}，本次处理 {len(todo)}", flush=True)
    if not todo:
        save(meta, emb)
        return

    model, proc, device = load_model()
    print(f"模型已加载，设备 {device}", flush=True)
    failed, t0 = [], time.time()
    for i in range(0, len(todo), BATCH):
        batch, imgs = [], []
        for it in todo[i : i + BATCH]:
            try:
                imgs.append(open_image(it["path"]))
                batch.append(it)
            except Exception as e:
                failed.append((it["id"], it["name"], repr(e)[:120]))
        if imgs:
            vecs = embed_images(model, proc, device, imgs)
            meta.extend(batch)
            emb.extend(vecs)
        n = i + BATCH
        if n % (BATCH * 25) == 0 or n >= len(todo):
            save(meta, emb)
            rate = min(n, len(todo)) / (time.time() - t0)
            print(f"{min(n, len(todo))}/{len(todo)}  {rate:.1f} 张/秒", flush=True)
    save(meta, emb)
    print(f"完成：索引 {len(meta)} 张，失败 {len(failed)} 张", flush=True)
    if failed:
        (INDEX_DIR / "failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1))
        for f in failed[:10]:
            print("  失败:", f)


if __name__ == "__main__":
    main()
