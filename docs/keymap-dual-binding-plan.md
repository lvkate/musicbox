# 键位双绑定改造计划（普通用户友好方向键支持）

> 状态：已实施
> 交付物：代码改造 + 帮助页更新 + README 更新 + 测试
> 涉及范围：`NEMbox/menu.py`、`NEMbox/cmd_parser.py`、`NEMbox/ui.py`、`NEMbox/config.py`（新增一个开关项）、`tests/`、`README.md`

---

## 1. 设计目的

当前 TUI 键位全面 Vim 化（`h/j/k/l` 导航、`u/d` 翻页、`g/G` 首尾、`[`/`]` 切歌），
对非 Vim 用户极不友好。本计划以**双绑定（additive dual-binding）**方式为重要功能
增加普通用户无需记忆即可直觉使用的键位（方向键、PgUp/PgDn、Home/End、F1 等），
同时保证：

- 原有键位全部保留，老用户肌肉记忆零影响；
- 用户自定义 keymap 配置（`~/.netease-musicbox/config.json`）行为不变；
- 数字前缀复合输入（`10j`、`25G`、`3]`）不受影响；
- 不为低频功能做无意义的全量双绑，控制改动面。

另外在 TUI 屏幕底部新增**当前界面可用键位指示栏**（需求 B）：以 nano/htop
风格常驻显示当前上下文可用的核心键位，让普通用户不依赖记忆和帮助页即可操作。
指示栏随界面切换（`datatype` 变化）自动更新，并提供配置开关供老用户关闭。

## 2. 现状机制摘要（已核对源码）

- 默认键位表：`NEMbox/config.py` 第 178–218 行 `default_config["keymap"]`，值为单字符字符串。
- 事件分发：`NEMbox/menu.py` 主循环 `start()`（第 643–1059 行），长 if/elif 链，
  字符键通过 `curses.keyname(key).decode("utf-8") == KEY_MAP["..."]` 比较；
  特例：前进额外兼容回车（`key == 10`，第 773 行）；
  鼠标滚轮映射为整数键码 259/258（第 53–61 行 `KEY_MAP["mouseUp"/"mouseDown"]`）。
- 数字前缀缓冲：主循环第 675–702 行 + `NEMbox/cmd_parser.py` 的 `parse_keylist()`。
  **关键事实**：curses 特殊键（方向键等）键码均 >255，不会进入
  `COMMAND_LIST`（由单字符 `ord()` 构成）、`range(48, 58)` 或 `[`/`]` 判断分支，
  因此会直接落到分发链，天然与数字前缀缓冲互不干扰。
- 巧合利好：`mouse_movement` 开启时滚轮上报的 258/259 恰等于 `curses.KEY_DOWN/KEY_UP`，
  硬绑方向键后鼠标逻辑行为完全一致，无副作用。
- Esc（键码 27）当前语义：清空输入缓冲（第 699–702 行）。
- 帮助页：`menu.py` 第 64–103 行 `shortcut` 数组，按键 `y` 或主菜单进入展示。
- README 键位表：`README.md` 第 153–188 行附近，需同步。

**UI 布局（需求 B 相关，`NEMbox/ui.py` 已核对）**：

- 屏幕分区固定：1–2 行播放信息（`build_playinfo`）、3 行进度条、4–5 行歌词
  （`build_process_bar`）、7 行标题、9 行起菜单项（`build_menu`）。
- `build_menu` 每次重绘先 `move(7,1); clrtobot()` 清掉第 7 行以下全部内容
  （第 397–398 行），指示栏必须挂在 `build_menu` 内部末尾绘制才能随重绘存活。
- 主循环每轮（约 `input_timeout`=500ms）调用一次 `build_menu_processbar()` 全量
  重绘，指示栏无需额外刷新机制，且 `datatype` 切换后自然更新。
- 菜单项最多绘制到 `step+8` 行，`step = max(int(ui.y * 4 / 5) - 10, 1)`
  （`menu.py` 第 1054 行），即底部约 1/5 屏高为空区，可容纳指示栏。
- `datatype` 已区分界面上下文：`main`/`songs`/`fmsongs`/`djprograms`/`comments`/
  `help`/`albums`/`artists`/`toplists` 等，可直接作为指示栏内容的分发键。
- 宽度工具现成：`truelen_cut()` 处理中英文混排截断，`self.content_width` 为
  内容区宽，配色可用 `curses.A_DIM` 或 `color_pair`。

## 3. 设计方案

### 3.1 键位映射表

P0（第一梯队，必做，风险最低收益最大）：

| 功能 | 原键（保留） | 新增键 | curses 键码 |
|---|---|---|---|
| 上移 / 下移 | `k` / `j` | `↑` / `↓` | `KEY_UP=259` / `KEY_DOWN=258` |
| 后退 / 前进 | `h` / `l`（前进另有 Enter） | `←` / `→` | `KEY_LEFT=260` / `KEY_RIGHT=261` |
| 上/下翻页 | `u` / `d` | `PgUp` / `PgDn` | `KEY_PPAGE=339` / `KEY_NPAGE=338` |
| 顶部 / 底部 | `g` / `G` | `Home` / `End` | `KEY_HOME=262` / `KEY_END=360` |
| 音量+ | `+` | `=`（同物理键免 Shift） | `ord('=')=61`，走字符匹配 |
| 帮助 | `y` | `F1` | `KEY_F1=265`（`KEY_F0+1`） |

P1（第二梯队，选做，逐个评估）：

| 功能 | 原键（保留） | 新增键 | 备注 |
|---|---|---|---|
| 返回上一层 | `h` | `Esc` | 语义见 3.2 |
| 上/下一曲 | `[` / `]` | `Shift+←` / `Shift+→` | 终端支持率一般，`getattr(C, "KEY_SLEFT", 393)` 兜底 |
| 搜索 | `f` | `Ctrl+F`（键码 6） | 通用搜索惯例 |

### 3.2 Esc 语义设计

当前 Esc 用于清空数字前缀缓冲。改造后语义为分层递进：

1. 输入缓冲非空（如按了一半的 `12j`）→ 清空缓冲（维持现状）；
2. 缓冲为空且不在主菜单 → 执行 `back_page_event()`（后退一层）；
3. 缓冲为空且在主菜单 → 无操作（防止误触退出，退出仍由 `q` 承担）。

### 3.3 不做双绑的功能（保持原键）

打碟 `a/z`、收藏 `s/c`、喜欢 `,`、缓存 `C`、FM 的 `.`/`/`、条目移动 `J/K`、
定时 `t`、播放模式 `P`、随机 `?`、退出 `q/w` 等低频功能。普通用户需要时
通过 `F1` 帮助页发现。

### 3.4 技术方案

1. **新增常量表**（建议放 `NEMbox/cmd_parser.py`，与 `KEY_MAP` 同源；或新建 `NEMbox/keymap.py`）：

   ```python
   import curses as C

   # 特殊键双绑定：动作 -> 整数键码列表（字符键不在此列）
   ALT_KEYS = {
       "up": [C.KEY_UP],
       "down": [C.KEY_DOWN],
       "back": [C.KEY_LEFT],
       "forward": [C.KEY_RIGHT],
       "prevPage": [C.KEY_PPAGE],
       "nextPage": [C.KEY_NPAGE],
       "top": [C.KEY_HOME],
       "bottom": [C.KEY_END],
       "help": [C.KEY_F(1)],
       "prevSong": [getattr(C, "KEY_SLEFT", 393)],   # P1
       "nextSong": [getattr(C, "KEY_SRIGHT", 402)],  # P1
   }
   ```

2. **统一匹配辅助函数**，供 `menu.py` 分发链使用：

   ```python
   def match_key(key: int, action: str) -> bool:
       """字符匹配（可配置 keymap）或特殊键码匹配（固定双绑定）。"""
       if key < 0:
           return False
       if key in ALT_KEYS.get(action, []):
           return True
       return C.keyname(key).decode("utf-8") == KEY_MAP[action]
   ```

   仅改造 3.1 表中涉及的 `elif` 分支，其余分支保持原样，控制 diff 面。
   注意保留各分支现有的 `pre_key not in range(ord("0"), ord("9"))` 等守卫条件。

3. **音量 `=`**：在 `volume+` 分支追加 `or key == ord("=")`，不进 `ALT_KEYS`（它是字符键）。

4. **Esc 语义**：改造主循环第 699–702 行分支——缓冲为空时调用
   `back_page_event()`（主菜单下该方法需确认为空操作安全，必要时加
   `self.datatype != "main"` 守卫）。

5. **帮助页**：`shortcut` 数组为 P0 每项新增展示行，格式沿用现有
   `[按键, 英文名, 中文说明]`，例如 `["↑/k", "Up", "上移"]`。这是
   "不用记忆"目标的关键——键位必须能被普通用户发现。

6. **README**：在第 153–188 行键位表中为每个双绑功能补充新增键。

### 3.5 屏幕底部键位指示栏（需求 B）

**形态**：单行常驻指示栏，绘制在屏幕最后一行（`ui.y - 1`），nano/htop 风格。
每项格式 `按键:说明`，项间两个空格分隔，整行用 `truelen_cut` 按
`content_width` 截断，`A_DIM` 弱化显示避免喧宾夺主。屏高过小（`y < 15`）时
自动隐藏，避免与正文重叠。

**上下文内容表**（按 `datatype` 分发，每类只列 6–8 个最高频项，超出宽度截断）：

| datatype | 指示内容（示例） |
|---|---|
| `default`（兜底） | `↑↓:移动  Enter:进入  ←:返回  F1:帮助  q:退出` |
| `main` | `↑↓:选择  Enter:进入  F1:帮助  q:退出` |
| `songs`/`djprograms` | `↑↓:移动  Enter:评论  空格:播放  []:切歌  s:收藏  C:缓存  f:搜索  F1:帮助` |
| `fmsongs` | 同 songs，追加 `.:删除FM  /:下一FM` |
| `comments` | `↑↓:移动  PgUp/PgDn:翻页  ←:返回  F1:帮助` |
| `help` | `↑↓:移动  G:打开GitHub  ←:返回  q:退出` |
| 输入对话框（`get_param`/`build_timing` 等） | 不显示（这些路径不经 `build_menu`，天然豁免） |

**实现要点**：

1. `ui.py` 新增提示内容常量表 `KEY_HINTS = {datatype: [(键, 说明), ...]}` 与纯函数
   `format_hints(datatype, width) -> str`（纯函数便于单测）；新增
   `Ui.build_key_hints(datatype)` 负责绘制，在 `build_menu` 末尾、`refresh()`
   之前调用。
2. `config.py` 新增开关 `key_hints`（默认 `True`），老用户可关闭收回该行；
   关闭时 `build_key_hints` 直接返回。
3. 指示键位以"普通用户键"为主展示（如 `↑↓` 而非 `jk`），与需求 A 的双绑定
   方案联动；两项功能同批次交付，普通用户看到的永远是自己按得出的键。
4. `fmsongs` 等复合内容用 `"default"` 兜底 + 字典查找，不存在的 datatype
   一律落到 `default`，不做全 datatype 穷举。
5. 评论界面在 `step+10`/`step+12` 有额外绘制（`ui.py` 第 499–518 行），
   屏高正常时与最后一行不冲突；`y < 15` 的极小终端由隐藏规则兜底。

## 4. 实施步骤

按顺序执行，每个阶段独立可交付、可回滚：

**阶段一（P0 核心绑定）**
1. 在 `NEMbox/cmd_parser.py` 增加 `ALT_KEYS` 常量与 `match_key()` 辅助函数并导出。
2. 改造 `NEMbox/menu.py` 分发链中 P0 涉及的 8 个分支
   （up/down/back/forward/prevPage/nextPage/top/bottom、help、volume+）。
3. 更新 `shortcut` 帮助数组。
4. 新增 `tests/test_alt_keymap.py`：单测 `match_key()` 对特殊键码、
   原字符键、未绑定键的判定；单测 Esc 分支判定逻辑（如抽成函数）。
5. 运行第 6 节全部校验命令。

**阶段二（P1 增强绑定）**
6. Esc 分层语义改造（`menu.py` 第 699–702 行分支）。
7. `Shift+←/→` 切歌、`Ctrl+F` 搜索双绑，补齐帮助页与测试。
8. 回归验证 `mouse_movement=True/False` 两种配置下方向键与滚轮行为。

**阶段三（文档与收尾）**
9. 更新 `README.md` 键位表，并新增"底部键位指示栏"功能说明及 `key_hints`
   配置项文档。
10. 按仓库 codemap 流程同步文档：`codemap.mjs changes` → 更新 →
    `codemap.mjs update` → 再跑 `changes` 确认 "no changes detected"。
11. 人工 TUI 验收（第 5 节清单）。

**阶段四（需求 B：底部键位指示栏）**
12. `ui.py` 新增 `KEY_HINTS` 内容表与 `format_hints()` 纯函数。
13. `config.py` 新增 `key_hints` 开关（默认 `True`）。
14. `ui.py` 新增 `Ui.build_key_hints()`，挂入 `build_menu` 末尾绘制
    （`refresh()` 之前）；屏高 `< 15` 自动隐藏。
15. 新增 `tests/test_key_hints.py`：单测 `format_hints()` 的 datatype 分发、
    `default` 兜底、宽度截断（含中英文混排）、开关关闭时返回空。
16. 运行第 6 节全部校验命令 + 人工 TUI 验收。

## 5. 验收测试条件

**自动化（全部必须通过）**
- `uv run pytest -q --tb=short`：全绿，含新增 `test_alt_keymap.py`。
- `uv run ruff check` / `uv run ruff format --check`：无新增告警。
- `uv run ty check`：exit 0（基线约 11 条 warn，不新增）。
- `uv build`：成功。

**单测断言要点**
- `match_key(259, "up")` 为真；`match_key(ord("k"), "up")` 为真；
  `match_key(ord("x"), "up")` 为假。
- `match_key()` 命中用户自定义 keymap 改写后的字符键（可配置性回归）。
- `=` 触发 volume+；`+` 仍触发 volume+。
- Esc：缓冲非空仅清空；缓冲为空且非主菜单触发后退；主菜单无副作用。
- `format_hints("songs", 80)` 含播放/收藏项；未知 datatype 返回 `default`
  内容；宽度不足时截断不产生乱码（`truelen` 对齐）；`key_hints=False` 时不绘制。

**人工 TUI 验收（需真实 TTY，`uv run musicbox`）**
- 方向键 `↑↓←→`：列表移动、层级进退正常；`→` 与 Enter 行为一致。
- `PgUp/PgDn` 翻页、`Home/End` 跳首尾的位移量与 `u/d/g/G` 完全一致。
- `F1` 打开帮助页，帮助页中能看到全部新增键位展示。
- `=` 与 `+` 均增加音量。
- Esc：输入 `12` 后按 Esc 清空不跳行；再按 Esc 返回上一层；主菜单按 Esc 不退出。
- 回归：`10j`、`25G`、`3]`、空格播放、`[`/`]` 切歌、`q` 退出全部照旧。
- `mouse_movement` 开启时滚轮与方向键均正常。
- 指示栏：主菜单、歌曲列表、FM、评论、帮助页各自显示对应提示；从歌曲列表
  返回主菜单后提示随之切换；`key_hints=false` 时不显示；窗口拉窄时截断不
  错位、不出现 curses 报错；`y < 15` 时自动隐藏；输入对话框（搜索/定时）
  界面不出现指示栏。

## 6. 校验命令基线

```bash
uv run ruff check && uv run ruff format --check
uv run ty check        # exit 0 即通过（warn 属基线）
uv run pytest -q --tb=short
uv build
```

## 7. 风险与注意事项

- **终端差异**：`Shift+←/→` 依赖 terminfo，部分终端不上报；用 `getattr` 兜底，
  并在 README 标注该绑定为尽力支持。P0 各项（方向键/PgUp/PgDn/Home/End/F1）
  在主流终端（xterm/iTerm2/Terminal.app/tmux）均可靠。
- **tmux/远程**：确认 `TERM` 设置正确，否则 Home/End 键码可能不同；
  属于环境配置问题，不在代码内兼容。
- **不要动 `config.py` 默认 keymap**：双绑定是代码内固定补充，不进入用户
  配置文件，避免 `ord()` 多字符崩溃及配置兼容问题。
- **守卫条件保留**：up/down/prevSong/nextSong 分支的 `pre_key` 数字守卫
  必须原样保留，否则数字前缀复合输入会被误触发。
- **指示栏渲染安全**：`addstr` 写到屏幕最后一行最后一列时 curses 会抛
  `error`（历史已封装的 `addstr` 内部 try/except 可兜底，见 `ui.py` 第
  139–146 行），但截断宽度应预留 1 列余量；指示栏只在 `build_menu` 内绘制，
  不可挂到 `build_process_bar`（后者不经过 `clrtobot`，会残留）。
- **指示栏与歌词区不冲突**：指示栏在屏幕最后一行，歌词在 4–5 行、进度条在
  3 行，互不重叠；唯一重叠风险是 `help` 页脚（20–22 行）与极小终端，由
  `y < 15` 隐藏规则兜底。
