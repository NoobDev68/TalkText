"""Проверка механизма вставки: буфер + Ctrl+V в активное поле."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit  # noqa: E402

from app.win import paste_text  # noqa: E402

app = QApplication(sys.argv)
edit = QLineEdit()
edit.show()
edit.setFocus()
edit.activateWindow()


def do_paste() -> None:
    paste_text("Проверка вставки номер один")


def check() -> None:
    print("в поле:", repr(edit.text()))
    print("успех" if edit.text() == "Проверка вставки номер один" else "ПРОВАЛ")
    app.quit()


QTimer.singleShot(600, do_paste)
QTimer.singleShot(1600, check)
app.exec()
