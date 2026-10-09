# Chrome 标签组 → Obsidian 笔记：操作说明书（自包含版）

这份文档不依赖任何 skill 系统。把整份文件（含末尾的完整脚本）贴给任意 AI，
它就能照着把 Chrome 标签组整理进 Obsidian。

---

## 0. 任务定义

用户有一个 Chrome 标签组（例如「商业分析」），里面有一批视频和文章。
要产出一篇 Obsidian 笔记，包含：

- 嵌套无序列表（母块 = 视频 / 文章，子块 = 每条内容）
- 每条的链接、作者、1~2 个关键词双链
- 视频打 `#towatch`，文章打 `#toread`
- 用 SuperTags 插件对应标签的字段键名，在每条下面填 `键:: 值`

## 1. 最关键的一件事：数据在哪

**Chrome 的已保存标签组不在会话文件里。**

- ❌ `~/Library/Application Support/Google/Chrome/Default/Sessions/*`（`Tabs_*` / `Session_*`）
  —— 这些只是当前/最近窗口的会话快照，组已经关掉就查不到了。
- ✅ `~/Library/Application Support/Google/Chrome/Default/Sync Data/LevelDB/`
  —— 同步数据库，键前缀 `saved_tab_group-dt-<guid>`。这才是真身。

而且这个 LevelDB 的 SSTable 用 **Snappy 压缩**，普通工具读不了。
下面第 6 节给了一个**纯标准库**的 Python 脚本，直接用，别重写。

其它坑：

- value 长度为 0 的 key 是墓碑（已删除），要过滤。
- macOS 上 AppleScript 控制 Chrome 会报 `privilege violation (-10004)`（没授权自动化），别走这条路。

## 2. 默认环境（跟用户确认，允许覆盖）

| 项 | 默认 | 说明 |
|---|---|---|
| Obsidian 库 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/马自立` | 收藏类笔记放 `阅读收藏/`，缩进用 **Tab** |
| SuperTags 插件 | 插件目录 `supertags-local`，显示名「SuperTags（自用）」 | 原版 `supertags` 是未启用的，别看错 |
| Chrome 数据目录 | `~/Library/Application Support/Google/Chrome` | 脚本会自动探测，多 profile 都扫 |

## 3. 步骤

1. **读标签组**：跑脚本 `--list-groups` 看有哪些组，`--group X` 看某组内容。
2. **清洗**：
   - URL 去掉 `spm_id_from`、`vd_source`、`trackid` 等追踪参数，留干净的 BV 号 / `p/xxx`。
   - 标题去掉站点尾巴：`_哔哩哔哩_bilibili`、知乎的 `(99+ 封私信 / 3 条消息) `。
   - 按 URL 判类型：`bilibili.com/video`、`youtube.com/watch` → 视频；专栏/博客 → 文章。
3. **查作者**：B 站用官方 API（第 5 节）；知乎常被反爬，用正文自引用兜底。
4. **关键词**：每条 1~2 个 `[[关键词]]`。先搜库里有没有同名页，没有才新建。
5. **打标签填字段**：视频 `#towatch`，文章 `#toread`；字段键名见第 4 节。
6. **落库**：默认写成一篇汇总笔记，文末加「作者索引」「关键词索引」。

## 4. SuperTags 字段

先确认插件：`<库>/.obsidian/community-plugins.json` 里列的是已启用的；manifest 的 `name` 字段是显示名。
字段键名来自 `<库>/.obsidian/plugins/supertags-local/data.json` 里对应标签的 `frontmatterTemplate`。

键名 = `frontmatterTemplate` 的键 **+** `fields` 的键，两处都要读。
`fields` 格式是 `键: 默认值 # 可选值1, 可选值2`，`#` 后面是可选值（可以没有），有可选值时从里面挑。

**`#towatch` / `#待看`（视频，folder 影视与音乐/）**
```
frontmatterTemplate:
type: 作品
清单: "[[towatch]]"
def:
from: "[[{{source}}]]"
fields:
类别: # 电影, 剧集, 纪录片, 动画, 视频（B站）, 视频（YouTube）
状态: 想看 # 想看, 在看, 已看
作者:
```

**`#toread` / `#待读` / `#book`（文章，folder Books/）**
```
frontmatterTemplate:
清单: "[[toread]]"
def:
from: "[[{{source}}]]"
fields:
type: 书 # 书, 文章, 论文
状态: 想读 # 想读, 在读, 已读
author:
domain: []
```

**`#tolisten` / `#待听`**：同 `#towatch`，`清单: "[[tolisten]]"`，
`类别` 可选 播客 / 有声书 / 音乐 / 课程 / 视频（B站），`状态` 想听 / 在听 / 已听。

写法要点：

- 必须写成**列表子项** `键:: 值`（两个冒号），不是 `键: 值`。
- `作者`（待看 / 待听）和 `author`（待读）一个中文一个英文，别互换。
- 键名不能含 `:` `：` `[` `]` `#`。
- 文章填 `type:: 文章` 是 `fields` 里的正式可选值，不算偏离。
- 插件 `watchFolders` 通常只有 `日记/`，所以放在 `阅读收藏/` 的笔记不会被自动处理成新页面，
  字段只是预先填好——这条也要提醒用户。
- 设了 `fields` 的标签（待读 / 待看 / 待听，2026-10-10 起）会在「日记整理」时自动把字段插到
  `[[标签名]]` 下面；看板 `scripts/marker-board.js` 也按它们显示维度、筛选。

## 5. 查作者

**B 站**（免登录，最稳）：
```
GET https://api.bilibili.com/x/web-interface/view?bvid=<BV号>
Header User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36
Header Referer: https://www.bilibili.com/
```
取 `data.owner.name`（UP 主）和 `data.owner.mid`（UID，用来确认多个视频是否同一人）。

**知乎**：API 和网页都常被反爬。用能渲染页面的抓取工具读正文；
很多作者写过「文章目录」类汇总文，里面自引用是 `作者名：文章标题` 格式，拿一次就能覆盖他名下其它文章。

**其它**：YouTube 用 `oembed?format=json` 的 `author_name`；小红书的 `xsec_token` 别删；
拿不到就留空或写「未确认」，别猜。

## 6. 脚本：read_chrome_tabgroups.py

仅依赖 Python 3 标准库。

```bash
python3 read_chrome_tabgroups.py --list-groups
python3 read_chrome_tabgroups.py --group 商业分析
python3 read_chrome_tabgroups.py --group 商业分析 --json
python3 read_chrome_tabgroups.py --user-data-dir /path/to/Chrome --profile Default
```

源码：

```python
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
```

## 7. 完成前自查

- [ ] 条目数与 `--list-groups` 显示的计数一致
- [ ] 每个视频有 `#towatch`、每篇文章有 `#toread`
- [ ] 字段键名与插件模板逐字一致，无漏键
- [ ] 双链都指向确实存在（或确实该新建）的页面
- [ ] URL 已去掉追踪参数，标题已去掉站点尾巴
- [ ] 已提醒用户：`watchFolders` 只有 `日记/`，放在别的目录不会自动建页
