"""sem_search.py 的分块必须和 Obsidian「第二大脑」插件的 fsBlocks 一模一样：
内容哈希对不上，共用的向量缓存就全部失效、整库重算。

下面的期望值是照现在的切法记下来的。这个测试挂了，说明切法变了——
先确认插件那边也做了同样的改动，再更新这里的期望值。
"""
import sys

import pytest

from helpers import load

pytest.importorskip("numpy")
ss = load("skills/koubo-writer/scripts/sem_search.py", "sem_search")

NOTE = """---
def: "注意力是一种稀缺资源"
aliases: [专注]
---
# 注意力

第一段正文，讲注意力为什么稀缺。
第二行还属于同一段。

- 列表项一：心流需要整块时间
	- 子项：手机通知会打断
- 短
- 和 [[宝a]] 一起去的那次不算素材

```
代码块里的内容不该被切出来
```

| 表格 | 行 |
最后一段，结尾的总结句写在这里。
"""

JOURNAL = """- 今天读完《心流》，最大的感受是专注很难
	- 子块：作者说目标要清晰
- #衣橱 黑色麂皮切尔西靴 42码
普通段落在日记里不单独成块，长度也够长
- 1. 编号也算列表吗？看看
1. 真正的编号列表项写在这里
"""


def test_note_blocks():
    assert ss.blocks_of(NOTE, "注意力") == [
        (0, "注意力 注意力是一种稀缺资源"),
        (6, "第一段正文，讲注意力为什么稀缺。\n第二行还属于同一段。"),
        (9, "- 列表项一：心流需要整块时间\n\t- 子项：手机通知会打断"),
        (19, "最后一段，结尾的总结句写在这里。"),
    ]


def test_journal_blocks():
    assert ss.blocks_of(JOURNAL, "2025_11_04") == [
        (0, "- 今天读完《心流》，最大的感受是专注很难\n\t- 子块：作者说目标要清晰"),
        (2, "- #衣橱 黑色麂皮切尔西靴 42码"),
        (4, "- 1. 编号也算列表吗？看看"),
        (5, "1. 真正的编号列表项写在这里"),
    ]


def test_private_blocks_are_skipped():
    for link in ("[[宝a]]", "[[宝]]", "[[人物/宝a|她]]", "[[宝#那天]]"):
        assert ss.blocks_of(f"- 今天和 {link} 去看了电影，很开心", "2025_01_01") == []
    # 只是名字里带「宝」的页面不算
    assert ss.blocks_of("- 读了 [[宝藏岛]] 的第一章，很好看", "2025_01_01") != []


def test_empty_scope_exits_cleanly(tmp_path, monkeypatch, capsys):
    """范围里一个块都没有时应该给出提示退出，而不是在 numpy 索引上报错。"""
    (tmp_path / "日记").mkdir()
    (tmp_path / "日记" / "2020_01_01.md").write_text("- 很久以前的一条日记，有足够长的内容", encoding="utf-8")
    monkeypatch.setattr(ss, "VAULT", str(tmp_path))
    monkeypatch.setattr(ss, "CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(sys, "argv", ["sem_search.py", "随便", "--scope", "journal", "--since", "2030-01-01"])
    with pytest.raises(SystemExit) as e:
        ss.main()
    assert "没有可检索的块" in str(e.value.code)
