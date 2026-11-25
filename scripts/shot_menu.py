"""Снимок контекстного меню трея."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui import STYLES, MainWindow  # noqa: E402

app = QApplication(sys.argv)
app.setStyle("Fusion")
palette = QPalette()
for role, color in (
    (QPalette.Window, "#14161c"),
    (QPalette.WindowText, "#e8eaed"),
    (QPalette.Base, "#14161c"),
    (QPalette.Text, "#e8eaed"),
    (QPalette.Button, "#1b1e26"),
    (QPalette.ButtonText, "#e8eaed"),
):
    palette.setColor(role, QColor(color))
app.setPalette(palette)
app.setStyleSheet(STYLES)

window = MainWindow()
menu = window.tray._icon.contextMenu()


def show_menu() -> None:
    menu.popup(QPoint(200, 200))
    QTimer.singleShot(400, shoot)


def shoot() -> None:
    menu.grab().save(str(ROOT / "docs" / "tray_menu.png"))
    print("пункты меню:", [a.text() for a in menu.actions() if a.text()])
    app.quit()


QTimer.singleShot(600, show_menu)
app.exec()
