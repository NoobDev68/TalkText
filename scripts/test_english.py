"""Проверка режимов с лёгким Whisper base: английская фраза должна быть на латинице."""

import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtCore import QCoreApplication, QTimer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import models  # noqa: E402
from app.engines import Engines  # noqa: E402
from app.recognizer import MODE_AUTO, MODE_EN, MODE_RU, Recognizer  # noqa: E402


def load(path: Path):
    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sr))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    return audio


en = load(ROOT / ".tmp" / "en_test.wav")
ru = load(ROOT / ".tmp" / "golos" / "train_003.wav")

app = QCoreApplication(sys.argv)
recognizer = Recognizer(Engines())
results: list = []
languages: list = []
recognizer.results.connect(results.append)
recognizer.language.connect(languages.append)


def start() -> None:
    recognizer.submit(en, MODE_EN)
    recognizer.submit(en, MODE_AUTO)
    recognizer.submit(ru, MODE_AUTO)
    recognizer.submit(ru, MODE_RU)


def finish() -> None:
    print("движки:", sorted(models.available_engines()))
    print("языки:", languages)
    for item in results:
        print([(s, l, (t or "")[:60], e) for s, l, t, e, _ in item])
    app.quit()


recognizer.ready.connect(start)
recognizer.preload(["whisper_base", "gigaam", "gigaam_ml"])
QTimer.singleShot(60000, finish)
app.exec()
