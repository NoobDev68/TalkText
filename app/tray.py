"""Значок в системном трее: меню и смена иконки по состоянию записи."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

COLOR_IDLE = "#5b7cfa"
COLOR_RECORDING = "#ff5c7a"


def _pixmap(size: int, recording: bool) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(COLOR_RECORDING if recording else COLOR_IDLE))
    p.drawEllipse(0.5, 0.5, size - 1, size - 1)

    p.setBrush(QColor("#ffffff"))
    if recording:
        # Квадрат «стоп» — значок явно отличается от микрофона.
        side = size * 0.36
        x = (size - side) / 2
        p.drawRoundedRect(QRectF(x, x, side, side), side * 0.22, side * 0.22)
    else:
        # Микрофон: капсула, дужка и ножка.
        w, h = size * 0.22, size * 0.40
        x, y = (size - w) / 2, size * 0.16
        p.drawRoundedRect(QRectF(x, y, w, h), w / 2, w / 2)
        pen = QPen(QColor("#ffffff"), max(1.2, size * 0.07))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(size * 0.26, size * 0.30, size * 0.48, size * 0.40), 180 * 16, 180 * 16)
        p.drawLine(QPointF(size / 2, size * 0.70), QPointF(size / 2, size * 0.82))
    p.end()
    return pm


def make_icon(recording: bool) -> QIcon:
    icon = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        icon.addPixmap(_pixmap(size, recording))
    return icon


class Tray(QObject):
    toggle_window = Signal()
    toggle_recording = Signal()
    quit = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.available = QSystemTrayIcon.isSystemTrayAvailable()
        self._icon = QSystemTrayIcon(make_icon(False), self)

        menu = QMenu()
        self.show_action = QAction("Скрыть окно")
        self.record_action = QAction("Начать распознавание")
        # Ссылка на атрибуте обязательна: QAction без владельца удаляется сборщиком мусора,
        # и пункт молча исчезает из меню.
        self.quit_action = QAction("Закрыть TalkText")
        menu.addAction(self.show_action)
        menu.addAction(self.record_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        self._icon.setContextMenu(menu)

        self.show_action.triggered.connect(self.toggle_window)
        self.record_action.triggered.connect(self.toggle_recording)
        self.quit_action.triggered.connect(self.quit)
        self._icon.activated.connect(self._on_activated)

        if self.available:
            self._icon.show()
        self.set_recording(False)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_window.emit()

    def set_recording(self, recording: bool) -> None:
        self._icon.setIcon(make_icon(recording))
        self._icon.setToolTip("TalkText — слушаю" if recording else "TalkText — готов")
        self.record_action.setText("Остановить распознавание" if recording else "Начать распознавание")

    def set_window_visible(self, visible: bool) -> None:
        self.show_action.setText("Скрыть окно" if visible else "Показать окно")

    def notify(self, message: str) -> None:
        if self.available:
            self._icon.showMessage("TalkText", message, QSystemTrayIcon.Information, 2500)

    def hide(self) -> None:
        self._icon.hide()
