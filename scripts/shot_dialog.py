"""Снимок диалога выбора движков."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.dialogs import ModelsDialog  # noqa: E402

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
dialog = ModelsDialog()
dialog.show()


def shoot() -> None:
    dialog.grab().save(str(ROOT / "docs" / "models_dialog.png"))
    app.quit()


QTimer.singleShot(800, shoot)
app.exec()
print("сохранено")
