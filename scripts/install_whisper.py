"""Скачивание Whisper large-v3 (модель + CUDA) с прогрессом."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import models

last = [-999]


def progress(key: str, done: int, total: int) -> None:
    percent = int(done * 100 / total) if total else 0
    if percent - last[0] >= 5:
        last[0] = percent
        print(
            f"{models.MODELS[key].title}: {percent}% "
            f"({done / 1048576:.0f}/{total / 1048576:.0f} МБ)",
            flush=True,
        )


t0 = time.time()
models.install("whisper", progress)
print(f"готово за {time.time() - t0:.0f} с")
print("установлен:", models.installed("whisper"), "| cuda:", models.installed("cuda"))
