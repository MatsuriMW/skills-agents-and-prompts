"""vault_search.py 按块返回日记命中：带上上级块的首行，短叶子块扩到父块。"""
import re

import pytest

from helpers import load

vs = load("skills/vault-ask/scripts/vault_search.py", "vault_search")

JOURNAL = """- 早上
	- 读《心流》第三章
		- [[心流]]
	- 作者说目标清晰、即时反馈、挑战和能力匹配是进入心流的三个条件。我的体会是第三条最难：太简单会无聊，太难会焦虑，只有刚好够得着的时候才会忘了时间，写稿的时候偶尔能碰到一次 ^abc123
- 下午整理衣橱，和心流无关的一条
	- 子项
"""


@pytest.fixture
def vault(tmp_path, monkeypatch):
    (tmp_path / "日记").mkdir()
    (tmp_path / "日记" / "2025_06_04.md").write_text(JOURNAL, encoding="utf-8")
    monkeypatch.setattr(vs, "VAULT", str(tmp_path))
    return tmp_path


def test_short_leaf_widens_to_parent(vault):
    rx = re.compile(vs.build_pattern(["心流"], backlinks=True), re.I)
    blocks = vs.journal_hits("日记/2025_06_04.md", rx)
    assert len(blocks) == 1
    anc, text, ids = blocks[0]
    assert anc == ["- 早上"]
    assert text == ["\t- 读《心流》第三章", "\t\t- [[心流]]"]


def test_long_block_keeps_ancestors_and_id(vault):
    rx = re.compile(vs.build_pattern(["三个条件"], backlinks=False), re.I)
    (anc, text, ids), = vs.journal_hits("日记/2025_06_04.md", rx)
    assert anc == ["- 早上"]
    assert ids == ["abc123"]


def test_backlink_pattern():
    rx = re.compile(vs.build_pattern(["心流"], backlinks=True), re.I)
    for s in ("[[心流]]", "[[心流|flow]]", "[[心流#定义]]", "#心流 "):
        assert rx.search(s), s
    assert not rx.search("心流")


def test_journal_date():
    assert str(vs.journal_date("日记/2025_06_04.md")) == "2025-06-04"
    assert str(vs.journal_date("日记/2025-6-4.md")) == "2025-06-04"
    assert vs.journal_date("Concepts/心流.md") is None
