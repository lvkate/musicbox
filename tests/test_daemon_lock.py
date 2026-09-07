"""Tests for daemon/TUI lock-conflict reporting (daemon.lock_holder)."""

import json
import os

from NEMbox import cli
from NEMbox import daemon as daemon_mod
from NEMbox.const import Constant


def _tmp_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(Constant, "lock_path", str(tmp_path / "musicboxd.lock"))
    monkeypatch.setattr(Constant, "socket_path", str(tmp_path / "musicboxd.sock"))


def test_describe_holder():
    assert daemon_mod.describe_holder(("daemon", 12)) == "musicbox daemon（pid 12）"
    assert daemon_mod.describe_holder(("tui", 34)) == "TUI（pid 34）"
    assert daemon_mod.describe_holder(("tui", None)) == "TUI"
    assert daemon_mod.describe_holder(("free", None)) == "另一 musicbox 实例"


def test_lock_holder_free(monkeypatch, tmp_path):
    _tmp_paths(monkeypatch, tmp_path)
    assert daemon_mod.lock_holder() == ("free", None)


def test_lock_holder_tui_when_held(monkeypatch, tmp_path):
    _tmp_paths(monkeypatch, tmp_path)
    fd = daemon_mod.acquire_lock()
    assert fd is not None
    try:
        kind, pid = daemon_mod.lock_holder()
    finally:
        daemon_mod.release_lock(fd)
    assert kind == "tui"
    assert pid == os.getpid()


def test_lock_holder_daemon_when_socket_answers(monkeypatch, tmp_path):
    _tmp_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(daemon_mod, "is_daemon_running", lambda: True)
    kind, _pid = daemon_mod.lock_holder()
    assert kind == "daemon"


def test_control_autostart_reports_tui_when_tui_holds_lock(
    monkeypatch, capsys, tmp_path
):
    _tmp_paths(monkeypatch, tmp_path)
    fd = daemon_mod.acquire_lock()
    assert fd is not None
    try:
        monkeypatch.setattr(cli, "is_daemon_running", lambda: False)
        monkeypatch.setattr(cli, "spawn_daemon", lambda: False)
        code = cli.main(["pause", "--json"])
    finally:
        daemon_mod.release_lock(fd)
    assert code == 4
    err = json.loads(capsys.readouterr().err)
    assert err["error"]["type"] == "daemon_not_running"
    assert "TUI" in err["error"]["message"]
    assert "TUI" in err["error"]["hint"]
