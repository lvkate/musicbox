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


def test_build_key_hints_hides_below_menu_safe_height():
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: True)
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: (_ for _ in ()).throw(AssertionError(args))

    for ui.y in (14, 15, 19):
        assert ui.build_key_hints("songs") is None


def test_build_key_hints_hides_help_and_comments_until_footer_safe_height():
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: True)
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: (_ for _ in ()).throw(AssertionError(args))

    for datatype in ("help", "comments"):
        for ui.y in (21, 23):
            assert ui.build_key_hints(datatype) is None


def test_build_key_hints_draws_at_safe_menu_height():
    calls = []
    ui = Ui.__new__(Ui)
    ui.config = SimpleNamespace(get=lambda name: True)
    ui.y = 21
    ui.startcol = 1
    ui.content_width = 80
    ui.addstr = lambda *args: calls.append(args)

    ui.build_key_hints("songs")

    assert calls


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
