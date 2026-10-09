#!/usr/bin/env python3
"""
读取 Chrome「已保存标签组」(Saved Tab Groups) 的内容。

Chrome 把已保存的标签组存在同步数据库里（Sync Data/LevelDB），
而不是 Sessions/*.SNSS（那些只是当前/最近窗口的会话）。
LevelDB 的 SSTable 用 Snappy 压缩，标准库读不了，所以这里自带一个
纯 Python 的 Snappy raw 解压 + SSTable/WAL 解析 + protobuf 最小解码。

用法：
    python3 read_chrome_tabgroups.py                     # 列出所有 profile 的标签组
    python3 read_chrome_tabgroups.py --list-groups
    python3 read_chrome_tabgroups.py --group 商业分析
    python3 read_chrome_tabgroups.py --group 商业分析 --json
    python3 read_chrome_tabgroups.py --user-data-dir /path/to/Chrome --profile Default

依赖：仅 Python 3 标准库。
"""

import argparse
import json
import os
import re
import struct
import sys

# ---------------------------------------------------------------- 路径

def chrome_user_data_dirs():
    """按平台给出 Chrome 用户数据目录的候选。"""
    home = os.path.expanduser("~")
    cands = []
    if sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support", "Google")
        cands += [os.path.join(base, d) for d in ("Chrome", "Chrome Beta", "Chrome Canary", "Chromium")]
    elif sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA", "")
        base = os.path.join(local, "Google")
        cands += [os.path.join(base, d, "User Data") for d in ("Chrome", "Chrome Beta", "Chrome SxS")]
        cands.append(os.path.join(local, "Chromium", "User Data"))
    else:
        base = os.path.join(home, ".config")
        cands += [os.path.join(base, d) for d in ("google-chrome", "chromium", "google-chrome-beta")]
    return [c for c in cands if os.path.isdir(c)]


def leveldb_dirs(user_data_dir, profile=None):
    out = []
    for name in sorted(os.listdir(user_data_dir)):
        if profile and name != profile:
            continue
        d = os.path.join(user_data_dir, name, "Sync Data", "LevelDB")
        if os.path.isdir(d):
            out.append((name, d))
    return out


# ---------------------------------------------------------------- Snappy

def _varint(b, i):
    r = 0
    s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if not c & 0x80:
            return r, i
        s += 7


def snappy_decompress(data):
    """Snappy raw block format 解压。"""
    ulen, i = _varint(data, 0)
    out = bytearray()
    n = len(data)
    while i < n:
        tag = data[i]
        i += 1
        t = tag & 0x03
        if t == 0:  # literal
            l = tag >> 2
            if l >= 60:
                nb = l - 59
                l = int.from_bytes(data[i:i + nb], "little")
                i += nb
            l += 1
            out += data[i:i + l]
            i += l
        elif t == 1:  # copy, 1-byte offset
            length = 4 + ((tag >> 2) & 0x07)
            off = ((tag >> 5) << 8) | data[i]
            i += 1
        elif t == 2:  # copy, 2-byte offset
            length = 1 + (tag >> 2)
            off = int.from_bytes(data[i:i + 2], "little")
            i += 2
        else:  # copy, 4-byte offset
            length = 1 + (tag >> 2)
            off = int.from_bytes(data[i:i + 4], "little")
            i += 4
        if t != 0:
            start = len(out) - off
            if start < 0:
                raise ValueError("bad snappy offset")
            if off >= length:
                out += out[start:start + length]
            else:
                for k in range(length):
                    out.append(out[start + k])
    return bytes(out)


# ---------------------------------------------------------------- LevelDB

LEVELDB_MAGIC = 0xDB4775248B80FB57


def rd_varint(b, i):
    r = 0
    s = 0
    while i < len(b):
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if not c & 0x80:
            return r, i
        s += 7
    return None, i


def iter_block(raw):
    """遍历一个 leveldb block，产出 (key, value)。"""
    n = len(raw)
    if n < 4:
        return
    num_restarts = struct.unpack("<I", raw[n - 4:])[0]
    body_end = n - 4 - 4 * num_restarts
    i = 0
    last = b""
    while i < body_end:
        shared, i = rd_varint(raw, i)
        non_shared, i = rd_varint(raw, i)
        vlen, i = rd_varint(raw, i)
        if shared is None or non_shared is None or vlen is None:
            return
        kd = raw[i:i + non_shared]
        i += non_shared
        val = raw[i:i + vlen]
        i += vlen
        last = last[:shared] + kd
        yield last, val


def parse_sst(path):
    """解析一个 .ldb（SSTable）。返回 [(key, value)]。"""
    data = open(path, "rb").read()
    if len(data) < 48:
        return []
    footer = data[-48:]
    if struct.unpack("<Q", footer[-8:])[0] != LEVELDB_MAGIC:
        return []
    i = 0
    _, i = rd_varint(footer, i)          # metaindex offset
    _, i = rd_varint(footer, i)          # metaindex size
    ih_off, i = rd_varint(footer, i)
    ih_size, i = rd_varint(footer, i)

    idx = data[ih_off:ih_off + ih_size]
    if data[ih_off + ih_size] == 1:      # trailer 里的压缩类型字节
        idx = snappy_decompress(idx)

    out = []
    for _k, val in iter_block(idx):
        o, j = rd_varint(val, 0)
        s, j = rd_varint(val, j)
        blk = data[o:o + s]
        if data[o + s] == 1:
            blk = snappy_decompress(blk)
        for k, v in iter_block(blk):
            out.append((k, v))
    return out


def parse_log(path):
    """解析 .log（WAL / 写前日志）。返回 [(key, value)]。"""
    data = open(path, "rb").read()
    out = []
    buf = b""
    pos = 0
    block_size = 32768
    while pos < len(data):
        block = data[pos:pos + block_size]
        pos += block_size
        p = 0
        while p + 7 <= len(block):
            length = struct.unpack("<H", block[p + 4:p + 6])[0]
            rtype = block[p + 6]
            payload = block[p + 7:p + 7 + length]
            p += 7 + length
            if rtype == 1:
                out.append(payload)
            elif rtype == 2:
                buf = payload
            elif rtype == 3:
                buf += payload
            elif rtype == 4:
                buf += payload
                out.append(buf)
                buf = b""
            else:
                break
    pairs = []
    for rec in out:
        if len(rec) < 12:
            continue
        cnt = struct.unpack("<I", rec[8:12])[0]
        i = 12
        for _ in range(cnt):
            if i >= len(rec):
                break
            t = rec[i]
            i += 1
            kl, i = rd_varint(rec, i)
            if kl is None:
                break
            key = rec[i:i + kl]
            i += kl
            vl, i = rd_varint(rec, i)
            if vl is None:
                break
            val = rec[i:i + vl]
            i += vl
            pairs.append((t, key, val))
    return pairs


def load_leveldb(directory):
    """合并读整个 LevelDB：先 SSTable（旧），再 WAL（新）。"""
    kv = {}
    for fn in sorted(os.listdir(directory)):
        if fn.endswith(".ldb"):
            try:
                for k, v in parse_sst(os.path.join(directory, fn)):
                    kv[k] = v
            except Exception as e:
                print(f"  [warn] {fn}: {e}", file=sys.stderr)
    for fn in sorted(os.listdir(directory)):
        if fn.endswith(".log"):
            try:
                for t, k, v in parse_log(os.path.join(directory, fn)):
                    if v:
                        kv[k] = v
                    else:
                        kv.pop(k, None)
            except Exception as e:
                print(f"  [warn] {fn}: {e}", file=sys.stderr)
    return kv


# ---------------------------------------------------------------- protobuf

def pb_fields(b):
    i = 0
    n = len(b)
    while i < n:
        key, i = rd_varint(b, i)
        if key is None:
            return
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v, i = rd_varint(b, i)
            if v is None:
                return
            yield fn, "v", v
        elif wt == 2:
            l, i = rd_varint(b, i)
            if l is None:
                return
            yield fn, "b", b[i:i + l]
            i += l
        elif wt == 5:
            yield fn, "f", b[i:i + 4]
            i += 4
        elif wt == 1:
            yield fn, "d", b[i:i + 8]
            i += 8
        else:
            return


def pb_get(b, num):
    for fn, wt, v in pb_fields(b):
        if fn == num:
            return wt, v
    return None, None


def pb_str(v):
    try:
        return v.decode("utf8")
    except Exception:
        return None


# ---------------------------------------------------------------- 业务解析

GROUP_PREFIX = b"saved_tab_group-dt-"


GUID_RE = re.compile(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def guid_of_key(k):
    """key 形如 saved_tab_group-dt-<guid>（后面可能跟若干字节），把 guid 抠出来。"""
    m = GUID_RE.search(k)
    return m.group(0).decode() if m else k[len(GROUP_PREFIX):].decode("utf8", "replace")


def extract(kv):
    """
    EntityData: field 2 -> 实体
      组实体:  field 4 -> { 2: 组名, 3: color, 4: ... }
      标签实体: field 5 -> { 1: group_guid, 2: position, 3: url, 4: title }
    value 为空 = 已删除的墓碑，跳过。
    """
    groups = {}
    tabs = []
    for k, val in kv.items():
        if not k.startswith(GROUP_PREFIX) or not val:
            continue
        wt, ent = pb_get(val, 2)
        if wt != "b":
            continue
        guid = guid_of_key(k)
        wt5, tab = pb_get(ent, 5)
        if wt5 == "b":
            g = pb_get(tab, 1)[1]
            pos = pb_get(tab, 2)[1]
            url = pb_get(tab, 3)[1]
            title = pb_get(tab, 4)[1]
            tabs.append({
                "guid": guid,
                "group": pb_str(g) if g else None,
                "position": pos if isinstance(pos, int) else None,
                "url": pb_str(url) if url else None,
                "title": pb_str(title) if title else None,
            })
        else:
            wt4, gspec = pb_get(ent, 4)
            if wt4 == "b":
                name = pb_get(gspec, 2)[1]
                groups[guid] = {
                    "guid": guid,
                    "title": pb_str(name) if name else "(无标题)",
                    "tabs": [],
                }
    for t in tabs:
        if t["group"] in groups:
            groups[t["group"]]["tabs"].append(t)
    for g in groups.values():
        g["tabs"].sort(key=lambda t: (t["position"] if t["position"] is not None else 9999))
    return groups


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="读取 Chrome 已保存标签组")
    ap.add_argument("--user-data-dir", help="Chrome 用户数据目录，默认自动探测")
    ap.add_argument("--profile", help="只处理某个 profile，如 Default / 'Profile 1'")
    ap.add_argument("--list-groups", action="store_true", help="只列出标签组名")
    ap.add_argument("--group", help="只输出某个标签组（可按名或部分名匹配）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if args.user_data_dir:
        udds = [args.user_data_dir]
    else:
        udds = chrome_user_data_dirs()
    if not udds:
        print("找不到 Chrome 用户数据目录，请用 --user-data-dir 指定。", file=sys.stderr)
        sys.exit(1)

    all_groups = {}
    for udd in udds:
        for prof, ldb in leveldb_dirs(udd, args.profile):
            kv = load_leveldb(ldb)
            for gid, g in extract(kv).items():
                g["profile"] = prof
                g["user_data_dir"] = udd
                all_groups[f"{prof}:{gid}"] = g

    if not all_groups:
        print("没有找到已保存的标签组。（标签组是否已保存/开启同步？）", file=sys.stderr)

    if args.group:
        all_groups = {k: v for k, v in all_groups.items()
                      if args.group.lower() in (v["title"] or "").lower()}

    if args.json:
        print(json.dumps(list(all_groups.values()), ensure_ascii=False, indent=2))
        return

    if args.list_groups:
        for g in all_groups.values():
            print(f'- {g["title"]}  ({len(g["tabs"])} 个标签, profile={g["profile"]})')
        return

    for g in all_groups.values():
        print(f'\n# {g["title"]}  ({len(g["tabs"])} 个标签)')
        for t in g["tabs"]:
            print(f'  [{t["position"]}] {t["title"]}')
            print(f'      {t["url"]}')


if __name__ == "__main__":
    main()
