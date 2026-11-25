"""Снимки окна для README: полный и компактный режимы."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui import MODE_AUTO, STYLES, MainWindow  # noqa: E402

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
window.set_compact(False)
while window.current_mode() != MODE_AUTO:
    window._cycle_mode()
window._models_ready = True
window.show()
window.raise_()


def step_full() -> None:
    window.set_status("Готов")
    window._append_text("Афина, Алиса, скажи баланс карты Сбербанк.")
    window._append_text("Напоминание: завтра в 10 утра встреча по проекту.")
    window.grab().save(str(ROOT / "docs" / "screenshot.png"))

    window.set_compact(True)
    window.set_status("Слушаю…", "#c9d2ff")
    window._set_recording_visual(True)
    QTimer.singleShot(500, step_compact)


def step_compact() -> None:
    window.grab().save(str(ROOT / "docs" / "screenshot_compact.png"))
    app.quit()


QTimer.singleShot(900, step_full)
app.exec()
print("сохранено")
