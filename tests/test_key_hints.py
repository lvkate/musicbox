import curses
from types import SimpleNamespace

from NEMbox.ui import Ui, format_hints


def test_format_hints_songs_includes_play_and_favorite():
    hints = format_hints("songs", 80)

    assert "空格:播放" in hints
    assert "s:收藏" in hints


def test_format_hints_unknown_datatype_uses_default():
    assert format_hints("unknown", 80) == format_hints("default", 80)


def test_format_hints_truncates_at_display_width_without_splitting_chinese():
    hints = format_hints("default", 12)

    assert hints == "↑↓:移动  "
    assert len(hints.encode("utf-8")) > 12
    assert sum(2 if char > chr(127) else 1 for char in hints) <= 11


def test_build_key_hints_disabled_does_not_draw():
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: False)
    ui.y = 24
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: (_ for _ in ()).throw(AssertionError(args))

    assert ui.build_key_hints("songs") is None


def test_build_key_hints_hidden_on_small_terminal_does_not_draw():
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: True)
    ui.y = 14
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: (_ for _ in ()).throw(AssertionError(args))

    assert ui.build_key_hints("songs") is None


def test_build_key_hints_uses_dim_attribute():
    calls = []
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: True)
    ui.y = 24
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: calls.append(args)

    ui.build_key_hints("main")

    assert calls[0][0] == 23
    assert calls[0][1] == 1
    assert calls[0][3] == curses.A_DIM
