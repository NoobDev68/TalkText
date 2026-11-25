"""Картинка двух иконок трея для README."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRect, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.tray import make_icon  # noqa: E402

app = QApplication(sys.argv)
canvas = QPixmap(300, 96)
canvas.fill(QColor("#14161c"))
p = QPainter(canvas)
p.setRenderHint(QPainter.Antialiasing)

for index, (state, caption) in enumerate(((False, "не слушает"), (True, "слушает"))):
    x = 24 + index * 150
    p.drawPixmap(QRect(x, 12, 56, 56), make_icon(state).pixmap(56, 56))
    p.setPen(QColor("#9aa3b8"))
    font = QFont("Segoe UI", 9)
    p.setFont(font)
    p.drawText(QRect(x, 70, 130, 20), Qt.AlignLeft, caption)
p.end()
canvas.save(str(ROOT / "docs" / "tray_icons.png"))
print("сохранено")
