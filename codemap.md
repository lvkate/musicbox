# Repository Atlas: NetEase-MusicBox

## Project Responsibility
NetEase-MusicBox is a Python 3.10+ CLI/curses TUI client for NetEase Cloud Music.
It streams and caches music from `music.163.com` via a private, encrypted HTTP API,
plays it through local backends (`mpg123` for MP3, `mpv` for FLAC/hires), and exposes
both a keyboard-driven interactive TUI and a stateless, AI-agent-friendly CLI. The
curses TUI supports configurable Vim keys plus fixed P0/P1 dual bindings, layered
Esc behavior, and context-sensitive bottom key hints controlled by `key_hints`. A
resident `musicboxd` daemon owns single-owner playback and JSON-RPC control over a
Unix domain socket, so the CLI/TUI can drive playback without holding the terminal.

## System Entry Points
- `NEMbox/__main__.py` — package entry point; `start()` dispatches to the CLI when
  arguments are present, otherwise launches the curses TUI (acquiring the flock lock
  and forking the version-check child).
- `NEMbox/cli.py` — `main(argv)`: stateless, AI-agent-friendly CLI. Data commands
  (`search`, `song info|url`, `playlist show`, `toplist [--index N]`,
  `recommend songs|playlists`, `fm`, `comments`, `like`, `auth status|login|logout`,
  `artist`, `album`) call the `NetEase` API directly; control commands (`play` with
  `--id/--playlist/--index/--artist/--album/--songs/--limit`, `download --artist/
  --album/--songs/--playlist`, `pause`, `resume`, `toggle`, `stop`, `next [n]`,
  `prev [n]`, `volume`, `mode`, `seek`, `status`, `lyrics`, `queue list|add|play|
  clear`, `daemon start|stop|status|restart`) are forwarded to `musicboxd` over
  JSON-RPC. Every command accepts `--json`; `--quiet` emits a pipeable scalar. Exit
  codes drive agent flow: `2` invalid args, `3` not-logged-in (auth required), `4`
  daemon-not-running (auto-starts unless `--no-daemon-autostart`), `10` confirmation.
- `NEMbox/daemon.py` — `MusicboxDaemon.serve` / module `daemon.main`: the double-forked
  `musicboxd` resident process that owns the `Player`, the `flock` lock, and the
  JSON-RPC server on a Unix socket.
- `pyproject.toml` — manifest; console script `musicbox = NEMbox.__main__:start`;
  build backend `hatchling`; runtime deps (`pycryptodomex`, `rapidfuzz`, `requests`,
  `requests-cache`, `urllib3`, `qrcode`) and dev deps (`pytest`, `ruff`, `ty`,
  `pre-commit`).

## Directory Map (Aggregated)
| Directory | Responsibility Summary | Detailed Map |
|-----------|------------------------|--------------|
| `NEMbox/` | Core library: NetEase encrypted API client, curses TUI, keymap infrastructure (`ALT_KEYS`/`match_key`) with P0/P1 dual bindings and layered Esc handling, context-sensitive bottom key hints (`key_hints`), mpg123+mpv playback, desktop lyrics, single-owner playback daemon (JSON-RPC over Unix socket), stateless CLI, cache/storage/config persistence. | [View Map](NEMbox/codemap.md) |
