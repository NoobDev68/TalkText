"""Интеграция с Windows: вставка текста и поведение окна."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

user32 = ctypes.windll.user32


def make_noactivate(hwnd: int) -> None:
    """Не даёт окну забирать фокус: вставка всегда идёт в активное поле пользователя."""
    style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
    user32.SetWindowLongW(hwnd, -20, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)


def _send_ctrl_v() -> None:
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(ord("V"), 0, 0, 0)
    user32.keybd_event(ord("V"), 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def paste_text(text: str) -> None:
    """Кладёт текст в буфер обмена и вставляет Ctrl+V в активное окно.

    Прежнее содержимое буфера возвращается через мгновение, если пользователь
    не успел что-то скопировать сам.
    """
    if not text:
        return
    clipboard = QGuiApplication.clipboard()
    old = clipboard.text()
    clipboard.setText(text)
    QTimer.singleShot(30, _send_ctrl_v)
    if old:
        QTimer.singleShot(400, lambda: clipboard.setText(old))
