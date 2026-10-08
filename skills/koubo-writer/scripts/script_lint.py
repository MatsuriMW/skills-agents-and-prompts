#!/usr/bin/env python3
"""口播稿 / 长文的机械检查，外加导出提词版和分镜表。

  script_lint.py 稿子.md                 # 检查：时长、画面空白、情绪曲线、风格硬规则
  script_lint.py 稿子.md --clean         # 只输出要念的字（提词版），标注全部去掉
  script_lint.py 稿子.md --shotlist      # 按 [!画面] / [!声音] 标注生成「分镜与素材清单」表
  script_lint.py 稿子.md --form article  # 书面稿：不查画面和情绪线（设问、devil's advocate、信源照查，文章稿总章要求的）

它查的都是能数出来的东西；好不好听、像不像他，还得人读。
"""
import argparse, re, sys

CPM = 280            # 口播语速：字 / 分钟
GAP_SEC = 25         # 出镜之外，画面空白超过这么多秒就提醒
SKIP_SECTIONS = re.compile(r"情绪线|分镜|素材清单|来源|信源|待核|录制前|速查|附[：:]|参考")
CUE = re.compile(r"^>\s*\[!(节奏|画面|声音|配图)\]\s*(.*)$")
# 风格提示词「不要出现的东西」里能机械查的
FLIP = re.compile(r"(?:不是|并非|不在于|不只是)[^。！？!?\n]{1,40}?(?:而是|而在于)")
HEDGE = ["这是一个复杂的话题", "每个人情况不同", "仅供参考", "今天我想和大家聊聊", "今天想和大家聊", "大家好"]
DEVIL = re.compile(r"有人(?:就)?会(?:问|说)|你可能会(?:说|问|觉得)|当然.{0,20}(?:绝对|片面|极端)|反过来(?:说|想)|话说回来")


def spoken_len(s):
    """按能念出来的量算：汉字一个算一个，英文数字一串算一个。"""
    return len(re.findall(r"[㐀-鿿]", s)) + len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.%+-]*", s))


def clean_line(l):
    l = re.sub(r"【[^】]*】", "", l)                       # 【★ …】录制前提示
    l = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", l)   # 双链
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)          # 链接
    l = re.sub(r"\*\*|==|~|`", "", l)
    return l.strip()


def parse(text):
    """返回 [(小节名, [item])]；item = ('say', 原文行) 或 ('cue', 类型, 内容)。"""
    L = text.split("\n")
    i = 0
    if L and L[0] == "---":
        i = 1
        while i < len(L) and L[i] != "---":
            i += 1
        i += 1
    sections, cur, name, in_code = [], [], "（开头）", False
    for l in L[i:]:
        if l.startswith("```"):
            in_code = not in_code; continue
        if in_code:
            continue
        m = re.match(r"^#{1,3}\s+(.*)$", l)
        if m:
            if re.match(r"^#\s", l) and not cur:      # 文章大标题
                continue
            sections.append((name, cur)); name, cur = m.group(1).strip(), []
            continue
        c = CUE.match(l)
        if c:
            cur.append(("cue", c.group(1), c.group(2).strip())); continue
        if l.startswith(">") or l.startswith("|") or re.match(r"^\s*(---|\*\*\*)\s*$", l) or not l.strip():
            if not l.strip():
                cur.append(("blank",))
            continue
        cur.append(("say", l))
    sections.append((name, cur))
    return [(n, it) for n, it in sections if any(x[0] != "blank" for x in it) and not SKIP_SECTIONS.search(n)]


def mmss(sec):
    return "%d:%02d" % (sec // 60, sec % 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--shotlist", action="store_true")
    ap.add_argument("--form", choices=["koubo", "article"], default="koubo")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()
    secs = parse(text)

    if a.clean:
        for n, items in secs:
            print(f"\n【{n}】\n")
            prev_blank = True
            for it in items:
                if it[0] == "say":
                    print(clean_line(it[1])); prev_blank = False
                elif it[0] == "blank" and not prev_blank:
                    print(); prev_blank = True
        return

    # 逐项走一遍，算每句话的起始时间
    t = 0.0
    timeline = []      # (sec, section, kind, payload)
    for n, items in secs:
        for it in items:
            if it[0] == "say":
                timeline.append((t, n, "say", it[1])); t += spoken_len(clean_line(it[1])) / CPM * 60
            elif it[0] == "cue":
                timeline.append((t, n, it[1], it[2]))
    total = t

    if a.shotlist:
        print("| # | 时间 | 类型 | 内容 | 怎么来 | 对上的那句话 |\n| --- | --- | --- | --- | --- | --- |")
        k = 0
        for j, (ts, n, kind, payload) in enumerate(timeline):
            if kind not in ("画面", "声音", "配图"):
                continue
            k += 1
            parts = [p.strip() for p in re.split(r"[｜|]", payload)]
            typ = parts[0] if kind != "声音" else "声音"
            body = parts[1] if kind != "声音" and len(parts) > 1 else (payload if kind == "声音" else "")
            how = parts[2] if kind != "声音" and len(parts) > 2 else ""
            nxt = next((clean_line(x[3])[:18] for x in timeline[j + 1:] if x[2] == "say"), "")
            print(f"| {k} | {mmss(int(ts))} | {typ} | {body} | {how} | {nxt}… |")
        return

    chars = sum(spoken_len(clean_line(x[3])) for x in timeline if x[2] == "say")
    print(f"全文要念的字：{chars}，按 {CPM} 字/分钟约 {mmss(int(total))}\n")
    print("各节：")
    st = {}
    for ts, n, kind, payload in timeline:
        d = st.setdefault(n, {"chars": 0, "start": ts, "bold": 0, "intens": []})
        if kind == "say":
            d["chars"] += spoken_len(clean_line(payload)); d["bold"] += len(re.findall(r"\*\*[^*]+\*\*", payload))
        elif kind == "节奏":
            d["intens"] += [int(x) for x in re.findall(r"强度\s*(\d)", payload)]
    for n, d in st.items():
        it = "→".join(map(str, d["intens"])) or "没标"
        print(f"  {mmss(int(d['start']))}  {n[:22]:<22} {d['chars']:>5} 字 ≈ {mmss(int(d['chars'] / CPM * 60))}  强度 {it}")

    warn = []
    says = [x for x in timeline if x[2] == "say"]
    body = "\n".join(clean_line(x[3]) for x in says)
    raw = "\n".join(x[3] for x in says)

    for m in FLIP.finditer(body):
        warn.append(f"翻案句（他说这个句式像 AI，直接从正面下判断）：「{m.group(0)[:40]}」")
    for w in HEDGE:
        if w in body:
            warn.append(f"叠甲 / 寒暄式开场：「{w}」")
    for n, d in st.items():
        if d["bold"] > 1:
            warn.append(f"「{n[:16]}」一节有 {d['bold']} 处加粗，核心判断一节最多一句")
    short = [x for x in says if spoken_len(clean_line(x[3])) < 22]
    if len(says) >= 12 and len(short) / len(says) > 0.4:
        warn.append(f"{len(short)}/{len(says)} 段不到 22 个字——碎成一行一段了。句子之间要接住，说成连贯的一串")
    stars = len(re.findall(r"【★", text))

    # 文章稿总章要求每篇都有的（书面稿、口播稿都查）
    if "？" not in body and "?" not in body:
        warn.append("没有设问或反问")
    if not DEVIL.search(body):
        warn.append("没找到 devil's advocate（「那有人就会问了」「当然我这样说有点绝对」这一类）")
    if not re.search(r"^#{1,3}\s*.*(来源|信源)", text, re.M):
        warn.append("文末没有「信源」")
    if a.form == "koubo":
        # 画面空白：从上一个非「出镜」的画面算起，出镜标注会把计时归零（那是有意对着镜头说）
        cues = [x for x in timeline if x[2] == "画面"]
        if not cues:
            warn.append("全文没有任何 [!画面] 标注——视频层没做")
        else:
            last, last_say = 0.0, ""
            for ts, n, kind, payload in timeline + [(total, "", "画面", "")]:
                if kind == "画面":
                    if ts - last > GAP_SEC:
                        warn.append(f"{mmss(int(last))}–{mmss(int(ts))} 有 {int(ts - last)} 秒没有画面标注（从「{last_say[:14]}…」起）。是连续讲抽象的东西，还是该标成出镜？")
                    last, last_say = ts, ""
                elif kind == "say" and not last_say:
                    last_say = clean_line(payload)
            kinds = [re.split(r"[｜|]", x[3])[0].strip() for x in cues]
            vague = [x[3] for x in cues if len(re.split(r"[｜|]", x[3])) < 2 or re.search(r"相关画面|相关素材|合适的", x[3])]
            for v in vague[:5]:
                warn.append(f"画面标注不够具体（要具体到能照着做）：「{v[:30]}」")
            from collections import Counter
            print("\n画面：" + "、".join(f"{k} {v}" for k, v in Counter(kinds).most_common()))
        # 情绪曲线
        seq = [(ts, int(m)) for ts, n, kind, p in timeline if kind == "节奏" for m in re.findall(r"强度\s*(\d)", p)]
        if not seq:
            warn.append("没有 [!节奏] 标注——情绪线没做")
        else:
            peak_t = max(seq, key=lambda x: x[1])[0]
            if total and peak_t < total * 0.6:
                warn.append(f"强度最高点在 {mmss(int(peak_t))}，全片 {mmss(int(total))}——峰值应该靠近结尾（峰终）")
            if seq[0][1] < 3:
                warn.append(f"开场强度只有 {seq[0][1]}——开头十五秒要有场景和悬着的问题，不要慢慢爬")
            run = 1
            for (t1, a1), (t2, a2) in zip(seq, seq[1:]):
                run = run + 1 if a1 == a2 else 1
                if run == 3:
                    warn.append(f"{mmss(int(t2))} 附近强度连续三段都是 {a2}——该换挡了")
            last_sec = list(st.items())[-1]
            if last_sec[1]["chars"] / CPM * 60 > 75 and peak_t < last_sec[1]["start"]:
                warn.append(f"最后一节「{last_sec[0][:14]}」有 {mmss(int(last_sec[1]['chars'] / CPM * 60))}，高点之后拖得太长")

    print(f"\n【★】待刷新的数字：{stars} 处")
    if warn:
        print(f"\n要看一眼的 {len(warn)} 处：")
        for w in warn:
            print("  · " + w)
    else:
        print("\n机械检查没发现问题。")


if __name__ == "__main__":
    main()
