"""Пути приложения: работают и из исходников, и из собранного .exe.

В портативной сборке exe лежит в папке приложения: модели и CUDA-библиотеки
хранятся рядом с ним (models/, vendor/nvidia), а упакованные ресурсы и onnx-asr —
внутри бандла PyInstaller.
"""

from __future__ import annotations

import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

# Папка бандла: у собранного exe это временная _internal, у исходников — корень проекта.
BUNDLE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))

# Папка приложения: рядом с exe (портативно) или корень проекта.
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else BUNDLE

MODELS_DIR = APP_DIR / "models"
RESOURCES_DIR = APP_DIR / "resources"
VENDOR_DIR = APP_DIR / "vendor"  # nvidia-библиотеки скачиваются сюда
BUNDLED_VENDOR = BUNDLE / "vendor"  # onnx-asr из бандла


def resource(name: str) -> Path:
    """Файл ресурса: сначала рядом с приложением, затем в бандле."""
    for base in (RESOURCES_DIR, BUNDLE / "resources"):
        path = base / name
        if path.is_file():
            return path
    return RESOURCES_DIR / name
