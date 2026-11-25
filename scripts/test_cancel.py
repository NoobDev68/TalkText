"""Проверка отмены скачивания и возобновления."""

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import models  # noqa: E402

models.uninstall("gigaam_ml")
print("перед скачиванием установлена:", models.installed("gigaam_ml"))

cancel = threading.Event()
last = [0]


def progress(key: str, done: int, total: int) -> None:
    percent = int(done * 100 / total) if total else 0
    if percent - last[0] >= 10:
        last[0] = percent
        print(f"  прогресс {percent}%")


threading.Thread(target=lambda: models.install("gigaam_ml", progress, cancel), daemon=True).start()
time.sleep(2.0)
cancel.set()
print("отправлена отмена")
time.sleep(2.5)

parts = [p for p in (ROOT / "models" / "gigaam-multilingual").glob("*.part")]
print("остались .part:", [p.name for p in parts], "| установлена:", models.installed("gigaam_ml"))

# Докачиваем заново — должно продолжиться и завершиться.
last[0] = 0
t0 = time.time()
models.install("gigaam_ml", progress)
print("дозагрузка завершена за", round(time.time() - t0, 1), "с | установлена:", models.installed("gigaam_ml"))
