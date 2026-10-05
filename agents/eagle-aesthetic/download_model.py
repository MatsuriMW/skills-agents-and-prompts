"""分块并行下载 SigLIP2 模型到 models/，可断点续传。单连接太慢，所以自己切块。

用法: .venv/bin/python download_model.py
"""
import concurrent.futures as cf
import os
import subprocess
import sys
from pathlib import Path

from common import MODEL_ID

BASE = f"https://huggingface.co/{MODEL_ID}/resolve/main"
DEST = Path(__file__).parent / "models" / MODEL_ID.split("/")[-1]
SMALL = ["config.json", "preprocessor_config.json", "tokenizer_config.json", "tokenizer.json", "special_tokens_map.json"]
BIG = "model.safetensors"
CHUNK = 32 * 1024 * 1024
WORKERS = 12
CURL = ["curl", "-sS", "-L", "--noproxy", "*", "--retry", "5", "--retry-all-errors"]


def size_of(url):
    out = subprocess.run(CURL + ["-I", url], capture_output=True, text=True, timeout=60).stdout
    return int([l for l in out.lower().splitlines() if l.startswith("content-length")][-1].split(":")[1])


def fetch_part(url, part, start, end):
    want = end - start + 1
    for _ in range(8):
        if part.exists() and part.stat().st_size == want:
            return
        subprocess.run(CURL + ["-m", "300", "-r", f"{start}-{end}", "-o", str(part), url])
    raise RuntimeError(f"分块下载失败 {part.name}")


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in SMALL:
        if not (DEST / name).exists():
            r = subprocess.run(CURL + ["-f", "-m", "120", "-o", str(DEST / name), f"{BASE}/{name}"])
            print(name, "ok" if r.returncode == 0 else "不存在，跳过", flush=True)
    final = DEST / BIG
    url = f"{BASE}/{BIG}"
    total = size_of(url)
    if final.exists() and final.stat().st_size == total:
        print("模型已存在")
        return
    parts_dir = DEST / "parts"
    parts_dir.mkdir(exist_ok=True)
    jobs = [(parts_dir / f"{i:04d}", s, min(s + CHUNK, total) - 1) for i, s in enumerate(range(0, total, CHUNK))]
    done = 0
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(fetch_part, url, p, s, e) for p, s, e in jobs]
        for f in cf.as_completed(futs):
            f.result()
            done += 1
            if done % 10 == 0 or done == len(jobs):
                print(f"{done}/{len(jobs)} 块", flush=True)
    with open(final, "wb") as out:
        for p, _, _ in jobs:
            out.write(p.read_bytes())
            os.remove(p)
    parts_dir.rmdir()
    assert final.stat().st_size == total
    print("模型下载完成", final, flush=True)


if __name__ == "__main__":
    sys.exit(main())
