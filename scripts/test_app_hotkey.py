"""Сквозная проверка: Right Ctrl+F12 в живом приложении."""

import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QImage  # noqa: E402

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.GetWindowDC.restype = wt.HDC
user32.GetWindowDC.argtypes = [wt.HWND]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.PrintWindow.argtypes = [wt.HWND, wt.HDC, ctypes.c_uint]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.GetDIBits.argtypes = [
    wt.HDC, wt.HBITMAP, ctypes.c_uint, ctypes.c_uint,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
]
user32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]

UP = 0x0002
EXT = 0x0001


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
        ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
        ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD),
    ]


def grab(hwnd) -> QImage:
    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)
    header = BITMAPINFOHEADER()
    header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    header.biWidth = w
    header.biHeight = -h
    header.biPlanes = 1
    header.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(header), 0)
    return QImage(buf, w, h, QImage.Format_RGB32).copy()


def has_red(hwnd, name: str) -> bool:
    image = grab(hwnd)
    image.save(str(ROOT / ".tmp" / name))
    red = 0
    for y in range(0, image.height(), 2):
        for x in range(0, image.width(), 2):
            c = image.pixelColor(x, y)
            if c.red() > 200 and c.green() < 130 and c.blue() < 160:
                red += 1
    return red > 200


def press(ctrl_vk: int, extended: bool) -> None:
    flags = EXT if extended else 0
    user32.keybd_event(ctrl_vk, 0x1D, flags, 0)
    time.sleep(0.05)
    user32.keybd_event(0x7B, 0, 0, 0)
    user32.keybd_event(0x7B, 0, UP, 0)
    time.sleep(0.05)
    user32.keybd_event(ctrl_vk, 0x1D, flags | UP, 0)


proc = subprocess.Popen([sys.executable, "main.py"], cwd=str(ROOT),
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
try:
    time.sleep(10)
    hwnd = user32.FindWindowW(None, "TalkText")
    print("до нажатия красная кнопка:", has_red(hwnd, "hk_before.png"))
    press(0xA3, True)  # Right Ctrl + F12
    time.sleep(1.2)
    print("после Right Ctrl+F12 красная кнопка:", has_red(hwnd, "hk_rec.png"), "(ожидается True)")
    press(0xA3, True)
    time.sleep(1.0)
    print("после остановки красная кнопка:", has_red(hwnd, "hk_stop.png"))
    press(0xA2, False)  # Left Ctrl + F12 — не должен включать
    time.sleep(1.2)
    print("после Left Ctrl+F12 красная кнопка:", has_red(hwnd, "hk_left.png"), "(ожидается False)")
finally:
    proc.terminate()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()
