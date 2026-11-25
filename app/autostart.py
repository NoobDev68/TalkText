"""Автозапуск TalkText при входе в Windows через ключ Run в реестре."""

from __future__ import annotations

import sys
import winreg
from pathlib import Path

from .paths import FROZEN

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.py"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
NAME = "TalkText"


def _pythonw() -> Path:
    """Интерпретатор без консольного окна."""
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return candidate if candidate.is_file() else exe


def command() -> str:
    if FROZEN:
        return f'"{Path(sys.executable).resolve()}"'
    return f'"{_pythonw()}" "{MAIN}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, NAME)
            return True
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, command())
        else:
            try:
                winreg.DeleteValue(key, NAME)
            except FileNotFoundError:
                pass
