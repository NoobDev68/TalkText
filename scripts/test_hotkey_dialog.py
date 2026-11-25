"""Проверка смены горячей клавиши через диалог настроек."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.dialogs import ModelsDialog
from app.hotkeys import HotkeySpec

QSettings("TalkText", "TalkText").remove("hotkey")

app = QApplication(sys.argv)
app.setStyle("Fusion")

dialog = ModelsDialog()
dialog.show()
app.processEvents()

print("текущая комбинация:", dialog.hotkey_btn.text())

dialog._start_capture()
event = QKeyEvent(QEvent.KeyPress, Qt.Key_F9, Qt.ControlModifier, 0, 0x78, 0)  # F9, Ctrl
QApplication.sendEvent(dialog, event)
app.processEvents()
print("после захвата:", dialog.hotkey_btn.text())

saved = HotkeySpec.from_json(QSettings("TalkText", "TalkText").value("hotkey"))
print("сохранено:", saved.label(), "| vk:", hex(saved.vk), "| ctrl:", saved.ctrl)

# Захват правого Ctrl + F10.
dialog._start_capture()
ctrl_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Control, Qt.ControlModifier, 0, 0xA3, 0)
QApplication.sendEvent(dialog, ctrl_event)
f10_event = QKeyEvent(QEvent.KeyPress, Qt.Key_F10, Qt.ControlModifier, 0, 0x79, 0)
QApplication.sendEvent(dialog, f10_event)
app.processEvents()
saved2 = HotkeySpec.from_json(QSettings("TalkText", "TalkText").value("hotkey"))
print("после правого Ctrl:", dialog.hotkey_btn.text(), "| ctrl:", saved2.ctrl, "| vk:", hex(saved2.vk))
