"""Проверка глобального хука: Right Ctrl+F12 срабатывает, Left Ctrl+F12 — нет."""

import ctypes
import ctypes.wintypes as wt
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, QTimer  # noqa: E402

from app.hotkeys import GlobalHotkey, HotkeySpec  # noqa: E402

user32 = ctypes.windll.user32
user32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]
user32.keybd_event.restype = None

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001


def press_combo(vk_ctrl: int, extended: bool) -> None:
    flags = KEYEVENTF_EXTENDEDKEY if extended else 0
    user32.keybd_event(vk_ctrl, 0x1D, flags, 0)
    time.sleep(0.05)
    user32.keybd_event(0x7B, 0, 0, 0)  # F12
    user32.keybd_event(0x7B, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    user32.keybd_event(vk_ctrl, 0x1D, flags | KEYEVENTF_KEYUP, 0)


app = QCoreApplication(sys.argv)
spec = HotkeySpec()  # Right Ctrl + F12
print("комбинация по умолчанию:", spec.label())
hotkey = GlobalHotkey(spec)
fired = []
hotkey.activated.connect(lambda: fired.append(time.time()))
hotkey.failed.connect(lambda msg: print("ОШИБКА ХУКА:", msg))
hotkey.start()
time.sleep(1.0)
print("хук:", hotkey._hook, "| поток жив:", hotkey._thread.is_alive() if hotkey._thread else None)

print("нажимаю Right Ctrl+F12…")
press_combo(0xA3, True)  # VK_RCONTROL
time.sleep(1.0)
print("сработало:", len(fired) == 1, "| ctrl_right:", hotkey._ctrl_right, "| fired-флаг:", hotkey._fired)

print("нажимаю Left Ctrl+F12…")
press_combo(0xA2, False)  # VK_LCONTROL
time.sleep(1.0)
print("после левого Ctrl срабатываний:", len(fired), "(ожидается 1)")
app.quit()
