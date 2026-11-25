"""Проверка автоопределения языка и выбора движка (без окна)."""

import sys
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engines import Engines  # noqa: E402
from app.recognizer import MODE_AB, MODE_AUTO, MODE_EN, MODE_RU, Recognizer  # noqa: E402


def load(path: Path):
    audio, sr = sf.read(str(path), dtype="float32")
    assert sr == 16000, sr
    return audio


ru = load(ROOT / ".tmp" / "golos" / "train_003.wav")
en = load(ROOT / ".tmp" / "libri" / "en_0.wav")

engines = Engines()
recognizer = Recognizer(engines)

for name, mode in [
    ("АВТО", MODE_AUTO),
    ("РУССКИЙ", MODE_RU),
    ("АНГЛИЙСКИЙ", MODE_EN),
    ("A/B", MODE_AB),
]:
    for lang_name, audio in (("ru-фраза", ru), ("en-фраза", en)):
        plan = recognizer._plan(audio, mode)
        print(f"{name:11} | {lang_name}: {plan}")
        for short, language in plan:
            try:
                text = engines.get(short).transcribe(audio, language=language)
                print(f"    {short:9} {str(language):5} -> {text[:70]}")
            except Exception as exc:  # noqa: BLE001
                print(f"    {short:9} ОШИБКА: {exc}")
