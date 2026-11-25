"""Проверка: крестик закрывает программу, «—» сворачивает в трей."""

import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

user32 = ctypes.windll.user32
user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.IsWindowVisible.argtypes = [wt.HWND]

proc = subprocess.Popen([sys.executable, "main.py"], cwd=str(ROOT),
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
try:
    time.sleep(10)
    hwnd = user32.FindWindowW(None, "TalkText")
    print("окно после старта:", bool(user32.IsWindowVisible(hwnd)))
    user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE — как кнопка ✕
    time.sleep(2.0)
    print("процесс завершился после крестика:", proc.poll() is not None, "| код:", proc.poll())
finally:
    proc.terminate()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()
