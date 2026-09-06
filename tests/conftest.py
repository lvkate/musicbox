"""Suite-wide isolation for tests.

Two `test_cli.py` paths used to touch the developer's real environment:

- `musicbox download` without `--path` writes MP3 files into the CWD,
  i.e. the repo root when pytest runs there.
- The QR-login success path calls `Storage.save()`, which overwrites the
  real `~/.netease-musicbox/database.json` with fake test users.

This autouse fixture keeps both inside `tmp_path`, so running pytest can
neither litter the repo nor clobber a real login.
"""

import pytest

from NEMbox.storage import Storage


@pytest.fixture(autouse=True)
def _isolate_real_user_state(monkeypatch, tmp_path):
    # Downloads default to the CWD when --path is omitted.
    monkeypatch.chdir(tmp_path)
    # Storage resolves real HOME-based paths once at import; redirect the
    # singleton's persistence targets and reset in-memory state so every
    # test starts from a pristine, throwaway database.
    storage = Storage()
    monkeypatch.setattr(storage, "storage_path", str(tmp_path / "database.json"))
    cookie_path = tmp_path / "cookie.txt"
    # A real NetEase() loads the cookie jar at construction; an empty
    # Netscape header keeps MozillaCookieJar.load() happy.
    cookie_path.write_text("# Netscape HTTP Cookie File\n")
    monkeypatch.setattr(storage, "cookie_path", str(cookie_path))
    storage.database = {
        "user": {"username": "", "password": "", "user_id": "", "nickname": ""},
        "collections": [],
        "songs": {},
        "player_info": {
            "player_list": [],
            "player_list_type": "",
            "player_list_title": "",
            "playing_order": [],
            "playing_mode": 0,
            "idx": 0,
            "ridx": 0,
            "playing_volume": 60,
        },
    }
