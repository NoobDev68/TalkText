"""Точка входа TalkText — плавающего окна распознавания русской речи."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QColor, QIcon, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import paths  # noqa: E402
from app.ui import STYLES, MainWindow  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("TalkText")
    app.setWindowIcon(QIcon(str(paths.resource("icon.png"))))
    app.setStyle("Fusion")
    # Окно живёт в трее: скрытие окна не должно завершать приложение.
    app.setQuitOnLastWindowClosed(False)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#14161c"))
    palette.setColor(QPalette.WindowText, QColor("#e8eaed"))
    palette.setColor(QPalette.Base, QColor("#14161c"))
    palette.setColor(QPalette.AlternateBase, QColor("#1b1e26"))
    palette.setColor(QPalette.Text, QColor("#e8eaed"))
    palette.setColor(QPalette.Button, QColor("#1b1e26"))
    palette.setColor(QPalette.ButtonText, QColor("#e8eaed"))
    palette.setColor(QPalette.Highlight, QColor("#3d55a8"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipBase, QColor("#1b1e26"))
    palette.setColor(QPalette.ToolTipText, QColor("#e8eaed"))
    app.setPalette(palette)
    app.setStyleSheet(STYLES)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
