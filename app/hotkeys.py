"""Глобальная горячая клавиша с поддержкой правого Ctrl.

RegisterHotKey не умеет отличать правый Ctrl от левого, поэтому используется
низкоуровневый хук WH_KEYBOARD_LL: он видит конкретную клавишу и не мешает
другим программам (клавиши не перехватываются, а только наблюдаются).
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import threading
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105

VK_F12 = 0x7B
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12

MODIFIER_VKS = {
    VK_LCONTROL,
    VK_RCONTROL,
    VK_LSHIFT,
    VK_RSHIFT,
    VK_LMENU,
    VK_RMENU,
    VK_LWIN,
    VK_RWIN,
    VK_SHIFT,
    VK_CONTROL,
    VK_MENU,
}

CTRL_NONE = ""
CTRL_LEFT = "left"
CTRL_RIGHT = "right"
CTRL_ANY = "any"

_KEY_NAMES = {
    0x20: "Space",
    0x0D: "Enter",
    0x09: "Tab",
    0x1B: "Esc",
    0x08: "Backspace",
    0x2D: "Insert",
    0x2E: "Delete",
    0x24: "Home",
    0x23: "End",
    0x21: "PageUp",
    0x22: "PageDown",
    0x25: "Left",
    0x26: "Up",
    0x27: "Right",
    0x28: "Down",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5", 0x75: "F6",
    0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    0x7C: "F13", 0x7D: "F14", 0x7E: "F15", 0x7F: "F16",
}

user32 = ctypes.windll.user32


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wt.DWORD),
        ("scanCode", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = wt.BOOL
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
user32.GetMessageW.restype = ctypes.c_int
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(wt.MSG), ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
]
user32.PeekMessageW.restype = wt.BOOL


def key_name(vk: int) -> str:
    if vk in _KEY_NAMES:
        return _KEY_NAMES[vk]
    if 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    return f"VK{vk}"


@dataclass(frozen=True)
class HotkeySpec:
    """Комбинация: клавиша + модификаторы (ctrl может быть левым или правым)."""

    vk: int = VK_F12
    ctrl: str = CTRL_RIGHT
    alt: bool = False
    shift: bool = False
    win: bool = False

    def label(self) -> str:
        parts = []
        if self.ctrl == CTRL_RIGHT:
            parts.append("Right Ctrl")
        elif self.ctrl == CTRL_LEFT:
            parts.append("Left Ctrl")
        elif self.ctrl == CTRL_ANY:
            parts.append("Ctrl")
        if self.alt:
            parts.append("Alt")
        if self.shift:
            parts.append("Shift")
        if self.win:
            parts.append("Win")
        parts.append(key_name(self.vk))
        return " + ".join(parts)

    def to_json(self) -> str:
        return json.dumps(
            {
                "vk": self.vk,
                "ctrl": self.ctrl,
                "alt": self.alt,
                "shift": self.shift,
                "win": self.win,
            }
        )

    @classmethod
    def from_json(cls, raw: str | None) -> "HotkeySpec":
        if not raw:
            return cls()
        try:
            data = json.loads(raw)
            return cls(
                vk=int(data.get("vk", VK_F12)),
                ctrl=str(data.get("ctrl", CTRL_RIGHT)),
                alt=bool(data.get("alt", False)),
                shift=bool(data.get("shift", False)),
                win=bool(data.get("win", False)),
            )
        except (ValueError, TypeError, json.JSONDecodeError):
            return cls()

    @classmethod
    def from_event(cls, vk: int, ctrl: str, alt: bool, shift: bool, win: bool) -> "HotkeySpec":
        return cls(vk=vk, ctrl=ctrl, alt=alt, shift=shift, win=win)


class GlobalHotkey(QObject):
    """Глобальный хук: срабатывает, когда нажата заданная комбинация."""

    activated = Signal()
    failed = Signal(str)

    def __init__(self, spec: HotkeySpec | None = None, parent=None) -> None:
        super().__init__(parent)
        self._spec = spec or HotkeySpec()
        self._thread: threading.Thread | None = None
        self._hook = None
        self._proc = None  # держим ссылку, иначе Python удалит callback
        self._ctrl_left = False
        self._ctrl_right = False
        self._alt = False
        self._shift = False
        self._win = False
        self._fired = False
        self._lock = threading.Lock()

    @property
    def spec(self) -> HotkeySpec:
        return self._spec

    def set_spec(self, spec: HotkeySpec) -> None:
        with self._lock:
            self._spec = spec
            self._fired = False

    def start(self) -> None:
        if self._thread is not None:
            return
        # Хук ставим в текущем (UI) потоке: так Windows доставляет ему события,
        # а отдельный поток лишь держит очередь сообщений живой.
        self._proc = HOOKPROC(self._callback)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0)
        if not self._hook:
            self.failed.emit("Не удалось установить глобальную горячую клавишу")
            return
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    # --- внутреннее ------------------------------------------------------------

    def _pump(self) -> None:
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            pass

    def _matches(self, vk: int) -> bool:
        with self._lock:
            spec = self._spec
        if vk != spec.vk:
            return False
        if self._alt != spec.alt or self._shift != spec.shift or self._win != spec.win:
            return False
        if spec.ctrl == CTRL_NONE:
            return not self._ctrl_left and not self._ctrl_right
        if spec.ctrl == CTRL_RIGHT:
            return self._ctrl_right
        if spec.ctrl == CTRL_LEFT:
            return self._ctrl_left
        return self._ctrl_left or self._ctrl_right

    def _callback(self, n_code, w_param, l_param):  # noqa: ANN001
        if n_code == 0:
            data = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk = data.vkCode
            down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
            if down:
                if vk == VK_LCONTROL:
                    self._ctrl_left = True
                elif vk == VK_RCONTROL:
                    self._ctrl_right = True
                elif vk in (VK_LMENU, VK_MENU):
                    self._alt = True
                elif vk in (VK_LSHIFT, VK_RSHIFT, VK_SHIFT):
                    self._shift = True
                elif vk in (VK_LWIN, VK_RWIN):
                    self._win = True
                elif vk not in MODIFIER_VKS:
                    if not self._fired and self._matches(vk):
                        self._fired = True
                        self.activated.emit()
            else:
                if vk == VK_LCONTROL:
                    self._ctrl_left = False
                elif vk == VK_RCONTROL:
                    self._ctrl_right = False
                elif vk in (VK_LMENU, VK_MENU):
                    self._alt = False
                elif vk in (VK_LSHIFT, VK_RSHIFT, VK_SHIFT):
                    self._shift = False
                elif vk in (VK_LWIN, VK_RWIN):
                    self._win = False
                else:
                    self._fired = False
        return user32.CallNextHookEx(None, n_code, w_param, l_param)
