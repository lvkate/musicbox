#!/usr/bin/env python
# __author__='walker'
"""
捕获类似curses键盘输入流,生成指令流
"""

import curses as C
from copy import deepcopy
from functools import wraps

from .config import Config

ERASE_SPEED = 5  # 屏幕5秒刷新一次 去除错误的显示

__all__ = [
    "ALT_KEYS",
    "cmd_parser",
    "match_key",
    "parse_keylist",
    "coroutine",
    "erase_coroutine",
]

KEY_MAP = Config().get("keymap")

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
    "help": [getattr(C, "KEY_F", lambda n: C.KEY_F0 + n)(1)],
    "prevSong": [getattr(C, "KEY_SLEFT", 393)],
    "nextSong": [getattr(C, "KEY_SRIGHT", 402)],
}


def match_key(key: int, action: str) -> bool:
    """字符匹配（可配置 keymap）或特殊键码匹配（固定双绑定）。"""
    if key < 0:
        return False
    if key in ALT_KEYS.get(action, []):
        return True
    return C.keyname(key).decode("utf-8") == KEY_MAP[action]


def coroutine(func):
    @wraps(func)
    def primer(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen

    return primer


def _cmd_parser():
    """
    A generator receive key value typed by user return constant keylist.
    输入键盘输入流,输出指令流,以curses默认-1为信号终止.
    """
    pre_key = -1
    keylist = []
    while 1:
        key = yield
        if key > 0 and pre_key == -1 or key > 0 and pre_key > 0:
            keylist.append(key)
        elif C.keyname(key).decode("utf-8") in KEY_MAP.values() and pre_key > 0:
            keylist.append(key)
            return keylist
        pre_key = key


def cmd_parser(results):
    """
    A generator manager which can catch StopIteration and start a new Generator.
    生成器管理对象,可以优雅地屏蔽生成器的终止信号,并重启生成器
    """
    while 1:
        results.clear()
        results += yield from _cmd_parser()
        yield results


def _erase_coroutine():
    keylist = []
    while 1:
        key = yield
        keylist.append(key)
        if len(set(keylist)) > 1 or len(keylist) >= ERASE_SPEED * 2:
            return keylist


def erase_coroutine(erase_cmd_list):
    while 1:
        erase_cmd_list.clear()
        erase_cmd_list += yield from _erase_coroutine()
        yield erase_cmd_list


def parse_keylist(keylist):
    """
    '2' '3' '4' 'j'  ----> 234 j
    supoort keys  [  ]   j  k  <KEY_UP> <KEY_DOWN>
    """
    keylist = deepcopy(keylist)
    if keylist == []:
        return None
    if (set(keylist) | {ord(KEY_MAP["prevSong"]), ord(KEY_MAP["nextSong"])}) == {
        ord(KEY_MAP["prevSong"]),
        ord(KEY_MAP["nextSong"]),
    }:
        delta_key = keylist.count(ord(KEY_MAP["nextSong"])) - keylist.count(
            ord(KEY_MAP["prevSong"])
        )
        if delta_key < 0:
            return (-delta_key, ord(KEY_MAP["prevSong"]))
        return (delta_key, ord(KEY_MAP["nextSong"]))
    tail_cmd = keylist.pop()
    if tail_cmd in range(48, 58) and (set(keylist) | set(range(48, 58))) == set(
        range(48, 58)
    ):
        return int("".join([chr(i) for i in keylist] + [chr(tail_cmd)]))

    if len(keylist) == 0:
        return (0, tail_cmd)
    if (
        tail_cmd
        in (
            ord(KEY_MAP["prevSong"]),
            ord(KEY_MAP["nextSong"]),
            ord(KEY_MAP["down"]),
            ord(KEY_MAP["up"]),
        )
        and max(keylist) <= 57
        and min(keylist) >= 48
    ):
        return (int("".join([chr(i) for i in keylist])), tail_cmd)
    return None


def main(data):
    """
    tset code
    测试代码
    """
    results = []
    group = cmd_parser(results)
    next(group)
    for i in data:
        group.send(i)
    group.send(-1)
    print(results)
    next(group)
    for i in data:
        group.send(i)
    group.send(-1)
    print(results)
    x = _cmd_parser()
    print("-----------")
    print(x.send(None))
    print(x.send(1))
    print(x.send(2))
    print(x.send(3))
    print(x.send(3))
    print(x.send(3))
    try:
        print(x.send(-1))
    except StopIteration as e:
        print(e.value)


if __name__ == "__main__":
    main(list(range(1, 12)[::-1]))
