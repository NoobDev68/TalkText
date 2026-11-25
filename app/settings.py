"""Настройки приложения в файле рядом с программой — для портативной сборки."""

from __future__ import annotations

from PySide6.QtCore import QSettings

from . import paths


def app_settings() -> QSettings:
    """settings.ini рядом с exe (или в корне проекта), без записей в реестр."""
    return QSettings(str(paths.APP_DIR / "settings.ini"), QSettings.IniFormat)
