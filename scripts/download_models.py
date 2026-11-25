"""Скачивание движков из командной строки (обёртка над app.models).

Примеры:
    python scripts/download_models.py gigaam
    python scripts/download_models.py gigaam_ml
    python scripts/download_models.py whisper
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import models  # noqa: E402

ALIASES = {
    "whisper": "whisper",
    "gigaam": "gigaam",
    "gigaam-v3": "gigaam",
    "gigaam-ml": "gigaam_ml",
    "gigaam_ml": "gigaam_ml",
    "cuda": "cuda",
}


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "gigaam"
    key = ALIASES.get(target)
    if key is None:
        print(f"неизвестный движок: {target}. Доступно: {', '.join(sorted(ALIASES))}")
        raise SystemExit(2)
    last = -1

    def progress(model_key: str, done: int, total: int) -> None:
        nonlocal last
        percent = int(done * 100 / total) if total else 0
        if percent != last:
            last = percent
            print(
                f"\r{models.MODELS[model_key].title}: {percent}% "
                f"({done / 1048576:.0f}/{total / 1048576:.0f} МБ)",
                end="",
                flush=True,
            )

    models.install(key, progress)
    print("\nготово")


if __name__ == "__main__":
    main()
