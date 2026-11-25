"""Общие элементы стиля: галочка чекбокса, читаемая на тёмном фоне."""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF

from . import paths

RESOURCES_DIR = paths.RESOURCES_DIR
_CHECK_PNG = RESOURCES_DIR / "check.png"


def ensure_check_icon() -> Path:
    """Рисует белую галочку для отмеченного чекбокса (32×32, с прозрачностью)."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    if _CHECK_PNG.is_file():
        return _CHECK_PNG
    image = QImage(32, 32, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#ffffff"), 3.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.drawPolyline([QPointF(7, 16.5), QPointF(13, 22.5), QPointF(25, 9.5)])
    painter.end()
    image.save(str(_CHECK_PNG))
    return _CHECK_PNG


def _gear_pixmap(size: int, color: str) -> QPixmap:
    """Шестерёнка с 8 зубцами и отверстием в центре."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))

    cx = cy = size / 2
    outer = size * 0.46
    inner = size * 0.34
    points = []
    teeth = 8
    for i in range(teeth * 2):
        angle = math.radians(i * 180 / teeth - 90)
        radius = outer if i % 2 == 0 else inner
        points.append(QPointF(cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    p.drawPolygon(QPolygonF(points))

    # Отверстие в центре — прозрачное, чтобы шестерёнка не выглядела диском.
    p.setCompositionMode(QPainter.CompositionMode_Clear)
    hole = size * 0.17
    p.drawEllipse(QPointF(cx, cy), hole, hole)
    p.end()
    return pm


def gear_icon(color: str = "#c7cddb") -> QIcon:
    icon = QIcon()
    for size in (14, 16, 18, 20, 24, 32):
        icon.addPixmap(_gear_pixmap(size, color))
    return icon


def _glyph_pixmap(size: int, recording: bool, color: str) -> QPixmap:
    """Белый микрофон (или квадрат «стоп») без фона — для кнопки записи."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    if recording:
        side = size * 0.36
        x = (size - side) / 2
        p.drawRoundedRect(QRectF(x, x, side, side), side * 0.22, side * 0.22)
    else:
        w, h = size * 0.22, size * 0.40
        x, y = (size - w) / 2, size * 0.16
        p.drawRoundedRect(QRectF(x, y, w, h), w / 2, w / 2)
        pen = QPen(QColor(color), max(1.2, size * 0.07))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(size * 0.26, size * 0.30, size * 0.48, size * 0.40), 180 * 16, 180 * 16)
        p.drawLine(QPointF(size / 2, size * 0.70), QPointF(size / 2, size * 0.82))
    p.end()
    return pm


def mic_icon(recording: bool = False, color: str = "#ffffff") -> QIcon:
    icon = QIcon()
    for size in (16, 20, 24, 28, 32, 48, 64):
        icon.addPixmap(_glyph_pixmap(size, recording, color))
    return icon


def check_qss() -> str:
    """QSS для заметного индикатора чекбокса."""
    path = ensure_check_icon().as_posix()
    return f"""
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.32);
    background: rgba(255, 255, 255, 0.05);
}}
QCheckBox::indicator:hover {{
    border-color: rgba(255, 255, 255, 0.55);
    background: rgba(255, 255, 255, 0.09);
}}
QCheckBox::indicator:checked {{
    background: #5b7cfa;
    border: 1px solid #5b7cfa;
    image: url("{path}");
}}
QCheckBox::indicator:checked:hover {{
    background: #6c8cff;
    border-color: #6c8cff;
}}
QCheckBox::indicator:disabled {{
    border-color: rgba(255, 255, 255, 0.16);
    background: transparent;
}}
QCheckBox::indicator:checked:disabled {{
    background: #3a4160;
    border-color: #3a4160;
}}
"""
