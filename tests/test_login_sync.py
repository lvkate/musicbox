"""Tests for the TUI live-session login gate (menu._sync_login_state).

The gate must trust the live `get_account_info()` session over the local
cache, so a stale/forged cached user can neither suppress the QR login nor
pollute request parameters. Transport failures report "unknown" and must
leave the cache alone (the gate then falls back to the cached identity).
"""

from types import SimpleNamespace

from NEMbox.menu import Menu, _sync_login_state


class FakeStorage:
    def __init__(self, user):
        self.database = {"user": dict(user)}
        self.saved = 0
        self.logged_out = 0

    def login(self, username, password, userid, nickname):
        self.database["user"] = {
            "username": username,
            "password": password,
            "user_id": userid,
            "nickname": nickname,
        }

    def logout(self):
        self.logged_out += 1
        self.database["user"] = {
            "username": "",
            "password": "",
            "user_id": "",
            "nickname": "",
        }

    def save(self):
        self.saved += 1


def _api(info):
    return SimpleNamespace(get_account_info=lambda: info)


def _raising_api():
    def _boom():
        raise ConnectionError("net down")

    return SimpleNamespace(get_account_info=_boom)


def test_sync_repairs_drifted_cache():
    storage = FakeStorage(
        {
            "username": "测试用户",
            "password": "",
            "user_id": 12345,
            "nickname": "测试用户",
        }
    )
    state, user = _sync_login_state(
        _api({"account": {"id": 1}, "profile": {"nickname": "真用户"}}), storage
    )
    assert state == "valid"
    assert user == {"user_id": 1, "nickname": "真用户"}
    assert storage.database["user"]["user_id"] == 1
    assert storage.database["user"]["nickname"] == "真用户"
    assert storage.saved == 1


def test_sync_leaves_matching_cache_untouched():
    storage = FakeStorage(
        {"username": "真用户", "password": "", "user_id": 1, "nickname": "真用户"}
    )
    state, user = _sync_login_state(
        _api({"account": {"id": 1}, "profile": {"nickname": "真用户"}}), storage
    )
    assert state == "valid"
    assert user == {"user_id": 1, "nickname": "真用户"}
    assert storage.saved == 0


def test_sync_reports_anonymous_without_session():
    storage = FakeStorage(
        {"username": "x", "password": "", "user_id": 1, "nickname": "x"}
    )
    assert _sync_login_state(_api({}), storage) == ("anonymous", None)
    # Sync itself never clears; the gate does that before scanning.
    assert storage.saved == 0


def test_sync_reports_anonymous_without_account_id():
    storage = FakeStorage(
        {"username": "", "password": "", "user_id": "", "nickname": ""}
    )
    assert _sync_login_state(_api({"profile": {"nickname": "u"}}), storage) == (
        "anonymous",
        None,
    )


def test_sync_reports_unknown_on_transport_failure():
    storage = FakeStorage(
        {"username": "真用户", "password": "", "user_id": 1, "nickname": "真用户"}
    )
    assert _sync_login_state(_api({"code": -1}), storage) == ("unknown", None)
    assert _sync_login_state(_raising_api(), storage) == ("unknown", None)
    assert storage.saved == 0
    assert storage.database["user"]["user_id"] == 1


def test_ensure_login_skips_qr_when_session_valid():
    storage = FakeStorage(
        {
            "username": "测试用户",
            "password": "",
            "user_id": 12345,
            "nickname": "测试用户",
        }
    )
    called = []
    stub = SimpleNamespace(
        api=_api({"account": {"id": 1}, "profile": {"nickname": "真用户"}}),
        storage=storage,
        login_suffix="（未登录）",
        login=lambda: called.append(True),
    )
    assert Menu._ensure_login(stub) is True
    assert called == []
    assert stub.login_suffix == ""
    assert storage.database["user"]["user_id"] == 1


def test_ensure_login_clears_dirty_cache_then_scans():
    storage = FakeStorage(
        {
            "username": "测试用户",
            "password": "",
            "user_id": 12345,
            "nickname": "测试用户",
        }
    )
    called = []
    stub = SimpleNamespace(
        api=_api({}),
        storage=storage,
        login_suffix="",
        login=lambda: called.append(True) or False,
    )
    assert Menu._ensure_login(stub) is False
    assert storage.logged_out == 1
    assert storage.saved == 1
    assert storage.database["user"]["username"] == ""
    assert called == [True]


def test_ensure_login_unknown_falls_back_to_cached_identity():
    storage = FakeStorage(
        {"username": "真用户", "password": "", "user_id": 1, "nickname": "真用户"}
    )
    called = []
    stub = SimpleNamespace(
        api=_api({"code": -1}),
        storage=storage,
        account="真用户",
        login_suffix="",
        login=lambda: called.append(True),
    )
    assert Menu._ensure_login(stub) is True
    assert called == []
    assert storage.saved == 0
    assert storage.logged_out == 0


def test_ensure_login_unknown_without_cache_scans():
    storage = FakeStorage(
        {"username": "", "password": "", "user_id": "", "nickname": ""}
    )
    called = []
    stub = SimpleNamespace(
        api=_raising_api(),
        storage=storage,
        account="",
        login_suffix="",
        login=lambda: called.append(True) or True,
    )
    assert Menu._ensure_login(stub) is True
    assert called == [True]
