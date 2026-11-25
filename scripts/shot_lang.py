"""Снимки интерфейса на русском и английском."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.dialogs import ModelsDialog  # noqa: E402
from app.i18n import set_language  # noqa: E402
from app.settings import app_settings  # noqa: E402
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

app_settings().setValue("language", "en")
set_language("en")
window = MainWindow()
window.set_compact(False)
while window.current_mode() != MODE_AUTO:
    window._cycle_mode()
window._models_ready = True
window.show()
window._append_text("Open the quarterly report and schedule a meeting.")
window.set_status("Ready")


def shoot_en() -> None:
    window.grab().save(str(ROOT / "docs" / "screenshot_en.png"))
    dialog = ModelsDialog()
    dialog.show()
    QTimer.singleShot(600, lambda: (dialog.grab().save(str(ROOT / "docs" / "models_dialog_en.png")), app.quit()))


QTimer.singleShot(900, shoot_en)
app.exec()
print("сохранено")
