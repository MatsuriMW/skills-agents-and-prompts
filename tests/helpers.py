import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(rel_path, name):
    """按文件路径导入脚本（skill 里的脚本不是包，没法直接 import）。"""
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
