"""Eagle 本地 API 与索引文件的公共读写。只读 Eagle，不写回。"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

EAGLE = "http://localhost:41595"
ROOT_FOLDER = "海报排版"
MODEL_ID = "google/siglip2-so400m-patch14-384"
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "tif", "tiff"}

HERE = Path(__file__).parent
INDEX_DIR = HERE / "index"
EMB_PATH = INDEX_DIR / "embeddings.npy"
META_PATH = INDEX_DIR / "meta.json"
REPORT_DIR = HERE / "reports"


def api(path, **params):
    url = f"{EAGLE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    # 本地接口不走代理
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=120) as r:
        return json.load(r)["data"]


def style_folders():
    """返回 (库路径, {folder_id: '日式设计/现代极繁'})，只含 ROOT_FOLDER 之下的文件夹。"""
    lib = api("/api/library/info")
    root = next(f for f in lib["folders"] if f["name"] == ROOT_FOLDER)
    out = {}

    def walk(f, prefix):
        for c in f.get("children", []):
            name = f"{prefix}/{c['name']}" if prefix else c["name"]
            out[c["id"]] = name
            walk(c, name)

    out[root["id"]] = ""
    walk(root, "")
    return lib["library"]["path"], out


def list_items():
    """ROOT_FOLDER 下全部图片条目，去重，带风格路径和原图路径。"""
    lib_path, folders = style_folders()
    seen = {}
    for fid in folders:
        for it in api("/api/item/list", folders=fid, limit=50000):
            if it["ext"].lower() not in IMAGE_EXTS or it.get("isDeleted"):
                continue
            if it["id"] in seen:
                continue
            styles = sorted(folders[f] for f in it.get("folders", []) if folders.get(f))
            seen[it["id"]] = {
                "id": it["id"],
                "name": it["name"],
                "ext": it["ext"],
                "styles": styles,
                "width": it.get("width"),
                "height": it.get("height"),
                "path": os.path.join(
                    lib_path, "images", f"{it['id']}.info", f"{it['name']}.{it['ext']}"
                ),
            }
    for it in seen.values():
        # Eagle 落盘时会替换文件名里的个别字符（如 … → ⋯），按名字找不到就看目录里的实际文件
        if not os.path.exists(it["path"]):
            d = os.path.dirname(it["path"])
            cands = [
                f
                for f in (os.listdir(d) if os.path.isdir(d) else [])
                if f != "metadata.json" and "_thumbnail." not in f
            ]
            if len(cands) == 1:
                it["path"] = os.path.join(d, cands[0])
    return list(seen.values())


def load_index():
    import numpy as np

    meta = json.loads(META_PATH.read_text())
    emb = np.load(EMB_PATH)
    assert len(meta) == len(emb), "索引与元数据条数不一致，请重跑 build_index.py"
    return meta, emb


def load_model():
    import torch
    from transformers import AutoModel, AutoProcessor

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    local = HERE / "models" / MODEL_ID.split("/")[-1]  # download_model.py 下载到这里
    src = str(local) if (local / "model.safetensors").exists() else MODEL_ID
    model = AutoModel.from_pretrained(src).to(device).eval()
    proc = AutoProcessor.from_pretrained(src)
    return model, proc, device


def _features(out):
    # 新版 transformers 返回带 pooler_output 的对象，旧版直接返回张量
    return out if hasattr(out, "norm") else out.pooler_output


def embed_images(model, proc, device, images):
    import torch

    with torch.no_grad():
        inputs = proc(images=images, return_tensors="pt").to(device)
        f = _features(model.get_image_features(**inputs))
        return (f / f.norm(dim=-1, keepdim=True)).float().cpu().numpy()


def embed_texts(model, proc, device, texts):
    import torch

    with torch.no_grad():
        inputs = proc(
            text=[t.lower() for t in texts], padding="max_length", max_length=64, truncation=True, return_tensors="pt"
        ).to(device)
        f = _features(model.get_text_features(**inputs))
        return (f / f.norm(dim=-1, keepdim=True)).float().cpu().numpy()
