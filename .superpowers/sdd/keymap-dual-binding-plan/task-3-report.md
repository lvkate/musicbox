# Task 3 实施报告

## 已实现行为

- 新增 `KEY_HINTS` 上下文提示表和纯函数 `format_hints(datatype, width)`。
- 支持 `default`、`main`、`songs`、`djprograms`、`fmsongs`、`comments`、`help`，未知上下文回退到 `default`。
- 提示以普通用户键位展示，项间使用两个空格，并按终端显示宽度截断，预留一列避免 curses 越界。
- `Ui.build_key_hints()` 在菜单重绘末尾、`refresh()` 前绘制最后一行，使用 `A_DIM`。
- `key_hints` 配置开关默认开启；终端高度小于 15 行时自动隐藏。
- 空菜单也会绘制提示栏；输入对话框路径未改动，因此不会显示提示栏。

## 测试命令与结果

- `uv run pytest -q tests/test_key_hints.py --tb=short`：6 passed
- `uv run ruff check && uv run ruff format --check`：通过
- `uv run ty check`：通过，11 条既有 warning，无新增诊断
- `uv run pytest -q --tb=short`：148 passed
- 全量测试生成的两个指定 MP3 测试产物已删除。

## 文件变更

- `NEMbox/ui.py`
- `NEMbox/config.py`
- `tests/test_key_hints.py`

## 自检

- 未改动默认 keymap、菜单、命令行解析或既有测试。
- 提示栏调用位于 `build_menu` 生命周期内，并覆盖空列表提前返回分支。
- 使用现有 `truelen_cut` 和 `addstr` 封装，保留中文混排安全截断与 curses 异常兜底。

## concerns

无。
