"""script_lint.py 是写稿流程的质量关卡，规则一直在加。这里用几篇小样稿把每条规则钉住，
免得改一条误伤别的。"""
import subprocess
import sys

from helpers import ROOT, load

SCRIPT = ROOT / "skills/koubo-writer/scripts/script_lint.py"
sl = load("skills/koubo-writer/scripts/script_lint.py", "script_lint")

GOOD = """---
选题: 测试
---
# 标题

## 一、开场

> [!节奏] 钩子 · 强度 4 · 观众：这不就是我吗
> [!画面] 出镜｜对着镜头，不切画面
假设说现在给你 100 万，没有外汇管制，可以自由投向全世界，你会怎么选？

## 二、展开

> [!节奏] 解释 · 强度 3 · 观众：原来如此
> [!画面] 字卡｜「美债 4.75%」「中债 1.68%」左右对比｜MG 动效
两张单子摆在你面前，差三个点，一百万一年就是三万块。有人就会问了，那为什么不全买美债。

## 三、落点

> [!节奏] 高点 · 强度 5 · 观众：被击中
> [!画面] 出镜｜对着镜头说完最后一句
因为汇率会把这三个点吃掉，而且吃得比你想的快。

## 来源
- 某某数据
"""


def run(text, tmp_path, *args):
    p = tmp_path / "稿子.md"
    p.write_text(text, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p), *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_spoken_len():
    assert sl.spoken_len("你好世界") == 4
    assert sl.spoken_len("GDP 增长 5.2%") == 4          # GDP、增、长、5.2%
    assert sl.spoken_len("，。！") == 0


def test_clean_line():
    assert sl.clean_line("看 [[2025_01_01|那天的日记]] 和 **重点** 【★ 待核】") == "看 那天的日记 和 重点"


def test_good_draft_passes(tmp_path):
    out = run(GOOD, tmp_path)
    assert "机械检查没发现问题" in out
    assert "画面：出镜 2、字卡 1" in out


def test_flags_style_problems(tmp_path):
    bad = GOOD.replace(
        "两张单子摆在你面前",
        "大家好，这不是钱的问题，而是认知的问题，我们要找到底层逻辑和抓手。**一**和**二**。两张单子摆在你面前",
    )
    out = run(bad, tmp_path)
    assert "翻案句" in out
    assert "「底层逻辑」" in out and "「抓手」" in out
    assert "「大家好」" in out
    assert "2 处加粗" in out


def test_flags_missing_parts(tmp_path):
    bare = "## 一\n\n只有一段话，没有标注，没有问号，也没有来源。\n"
    out = run(bare, tmp_path)
    for msg in ("没有设问或反问", "devil's advocate", "没有来源清单", "视频层没做", "情绪线没做"):
        assert msg in out


def test_flags_emotion_curve(tmp_path):
    curve = GOOD.replace("强度 4", "强度 2").replace("强度 5", "强度 1")
    out = run(curve, tmp_path)
    assert "开场强度只有 2" in out
    assert "峰值应该靠近结尾" in out


def test_flags_flat_intensity(tmp_path):
    flat = GOOD.replace("强度 4", "强度 3").replace("强度 5", "强度 3")
    assert "连续三段都是 3" in run(flat, tmp_path)


def test_flags_visual_gap_and_vague_cue(tmp_path):
    long_talk = "这一段在讲很抽象的道理，没有任何可以看的东西，一直在讲一直在讲。" * 6
    text = GOOD.replace("因为汇率会把", long_talk + "因为汇率会把").replace(
        "> [!画面] 出镜｜对着镜头说完最后一句", "> [!画面] 相关画面"
    )
    out = run(text, tmp_path)
    assert "秒没有画面标注" in out
    assert "画面标注不够具体" in out


def test_article_skips_video_checks(tmp_path):
    out = run("## 一\n\n只有一段话，没有标注，没有问号，也没有来源。\n", tmp_path, "--form", "article")
    assert "视频层没做" not in out and "devil's advocate" not in out


def test_clean_output(tmp_path):
    out = run(GOOD, tmp_path, "--clean")
    assert "[!" not in out and "来源" not in out
    assert "【一、开场】" in out
    assert "假设说现在给你 100 万" in out


def test_shotlist(tmp_path):
    rows = [l for l in run(GOOD, tmp_path, "--shotlist").splitlines() if l.startswith("| ") and "---" not in l]
    assert rows[0].startswith("| # | 时间 |")
    assert len(rows) == 4                                  # 表头 + 三条画面
    assert "| 字卡 | 「美债 4.75%」「中债 1.68%」左右对比 | MG 动效 |" in rows[2]
