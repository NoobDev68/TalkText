"""Характеристики компьютера и подбор движков под них.

Определяем видеокарту NVIDIA и объём её памяти (nvidia-smi), общий объём ОЗУ,
свободное место рядом с программой и число ядер. По этим данным выбираем движки,
которые имеют смысл на этой машине.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import shutil
import subprocess
from dataclasses import dataclass

from . import paths

# nvidia-smi не должен мигать консолью в оконном приложении.
_NO_WINDOW = 0x08000000


@dataclass(frozen=True)
class Hardware:
    cpu_cores: int
    ram_gb: float
    free_gb: float
    gpu: str  # пустая строка — видеокарта NVIDIA не найдена
    vram_gb: float

    @property
    def has_gpu(self) -> bool:
        return self.vram_gb > 0

    def describe(self) -> str:
        """Короткая строка для окна настроек."""
        if self.has_gpu:
            gpu = f"{self.gpu} ({self.vram_gb:.0f} ГБ)"
        else:
            gpu = "нет NVIDIA"
        return f"{gpu} · ОЗУ {self.ram_gb:.0f} ГБ · свободно {self.free_gb:.0f} ГБ"


def _ram_gb() -> float:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", wt.DWORD),
            ("dwMemoryLoad", wt.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0.0
    return status.ullTotalPhys / 1024**3


def _free_gb() -> float:
    try:
        return shutil.disk_usage(paths.APP_DIR).free / 1024**3
    except OSError:
        return 0.0


def _gpu() -> tuple[str, float]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return "", 0.0
    if result.returncode != 0 or not result.stdout.strip():
        return "", 0.0
    line = result.stdout.strip().splitlines()[0]
    name, _, memory = line.rpartition(",")
    try:
        vram = float(memory.strip()) / 1024
    except ValueError:
        return "", 0.0
    return name.strip(), vram


def detect() -> Hardware:
    gpu, vram = _gpu()
    return Hardware(
        cpu_cores=os.cpu_count() or 0,
        ram_gb=_ram_gb(),
        free_gb=_free_gb(),
        gpu=gpu,
        vram_gb=vram,
    )


def recommended_keys(hw: Hardware | None = None) -> set[str]:
    """Какие движки имеет смысл поставить на этой машине.

    GigaAM v3 — всегда: это лучший русский на процессоре, не боится шума.
    На видеокарте NVIDIA от 4 ГБ — Whisper large-v3-turbo для английского.
    Whisper-Podlodka-Turbo не рекомендуем автоматически: он точнее на чистой
    речи, но на шуме уступает GigaAM — пусть остаётся осознанным выбором.
    Без видеокарты — small, если хватает памяти, иначе base.
    """
    from . import models

    hw = hw or detect()
    keys = {"gigaam"}
    if hw.has_gpu and hw.vram_gb >= 4:
        keys.add("whisper_turbo")
    elif hw.ram_gb >= 8:
        keys.add("whisper_small")
    else:
        keys.add("whisper_base")

    # Не предлагаем то, что не поместится на диск: считаем суммарно, с запасом 1 ГБ.
    # GPU-движкам нужны ещё библиотеки CUDA — их вес тоже учитываем.
    budget = max(hw.free_gb - 1.0, 0.0)
    cuda_gb = models.MODELS["cuda"].size_mb / 1024
    cuda_ready = "cuda" in models.installed_keys()
    picked: set[str] = set()
    for key in ("gigaam", "whisper_turbo", "whisper_ru", "whisper_small", "whisper_base"):
        if key not in keys:
            continue
        spec = models.MODELS[key]
        cost = spec.size_mb / 1024
        needs_cuda = "cuda" in spec.requires and not cuda_ready
        if needs_cuda:
            cost += cuda_gb
        if cost <= budget:
            picked.add(key)
            budget -= cost
            if needs_cuda:
                cuda_ready = True
    return picked
