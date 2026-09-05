import curses as C
from types import SimpleNamespace

import pytest

from NEMbox import cmd_parser
from NEMbox.cmd_parser import ALT_KEYS, KEY_MAP, match_key
from NEMbox.menu import Menu, _handle_escape


@pytest.mark.parametrize(
    ("action", "key"),
    [
        ("up", C.KEY_UP),
        ("down", C.KEY_DOWN),
        ("back", C.KEY_LEFT),
        ("forward", C.KEY_RIGHT),
        ("prevPage", C.KEY_PPAGE),
        ("nextPage", C.KEY_NPAGE),
        ("top", C.KEY_HOME),
        ("bottom", C.KEY_END),
        ("help", C.KEY_F0 + 1),
    ],
)
def test_match_key_accepts_special_key_codes(action, key):
    assert key in ALT_KEYS[action]
    assert match_key(key, action)


def test_match_key_accepts_original_character_key(monkeypatch):
    monkeypatch.setattr(cmd_parser.C, "keyname", lambda key: chr(key).encode())

    assert match_key(ord("k"), "up")
    assert not match_key(ord("x"), "up")


@pytest.mark.parametrize("action", ["prevSong", "nextSong"])
def test_match_key_accepts_shift_arrow_key_codes(action):
    key = ALT_KEYS[action][0]

    assert match_key(key, action)


@pytest.mark.parametrize(
    ("pre_keylist", "key_list"),
    [([ord("1")], []), ([], [ord("1")])],
)
def test_escape_clears_pending_input_without_navigating(pre_keylist, key_list):
    assert not _handle_escape(pre_keylist, key_list, "songs")
    assert pre_keylist == []
    assert key_list == []


def test_escape_navigates_back_when_buffer_is_empty():
    assert _handle_escape([], [], "songs")


def test_escape_is_noop_on_main_menu():
    pre_keylist = []
    key_list = []

    assert not _handle_escape(pre_keylist, key_list, "main")
    assert pre_keylist == []
    assert key_list == []


def test_match_key_uses_custom_character_keymap(monkeypatch):
    monkeypatch.setattr(cmd_parser.C, "keyname", lambda key: chr(key).encode())
    monkeypatch.setitem(KEY_MAP, "up", "x")

    assert match_key(ord("x"), "up")
    assert not match_key(ord("k"), "up")


class _FakeScreen:
    def __init__(self, keys):
        self.keys = iter(keys)

    def timeout(self, _value):
        return None

    def getch(self):
        return next(self.keys)

    def refresh(self):
        return None


class _FakePlayer:
    def __init__(self):
        self.volume_up_calls = 0

    def volume_up(self):
        self.volume_up_calls += 1

    def update_size(self):
        return None

    def stop(self):
        return None


def _run_volume_key(key, monkeypatch):
    player = _FakePlayer()
    screen = _FakeScreen([key, ord("q")])
    menu = Menu.__new__(Menu)
    menu.ui = SimpleNamespace(
        screen=screen,
        y=40,
        build_menu=lambda *args: None,
        update_size=lambda: None,
    )
    menu.screen = screen
    menu.config = SimpleNamespace(
        get=lambda name: {
            "input_timeout": 0,
            "mouse_movement": False,
            "page_length": 10,
        }[name]
    )
    menu.player = player
    menu.cache = SimpleNamespace(quit=lambda: None)
    menu.storage = SimpleNamespace(save=lambda: None)
    menu.datatype = "main"
    menu.title = ""
    menu.datalist = []
    menu.offset = 0
    menu.index = 0
    menu.step = 10
    menu.menu_starts = 0
    menu.stack = []
    menu.key_list = []
    menu.pre_keylist = []
    menu.quit = False
    menu.build_menu_processbar = lambda: None

    monkeypatch.setattr("NEMbox.menu.show_lyrics_new_process", lambda: None)
    monkeypatch.setattr("NEMbox.menu.stop_lyrics_process", lambda: None)
    monkeypatch.setattr("NEMbox.menu.C.endwin", lambda: None)
    monkeypatch.setattr(cmd_parser.C, "keyname", lambda value: chr(value).encode())

    menu.start()
    return player.volume_up_calls


@pytest.mark.parametrize("key", [ord("+"), ord("=")])
def test_volume_up_accepts_original_and_unshifted_character(key, monkeypatch):
    assert _run_volume_key(key, monkeypatch) == 1
