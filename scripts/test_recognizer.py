"""Проверка полной цепочки Recognizer: очередь, LID, выбор движка."""

import sys
from pathlib import Path

import soundfile as sf
from PySide6.QtCore import QCoreApplication, QTimer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engines import Engines  # noqa: E402
from app.recognizer import MODE_AB, MODE_AUTO, Recognizer  # noqa: E402

app = QCoreApplication(sys.argv)
recognizer = Recognizer(Engines())
results: list = []
languages: list = []
recognizer.results.connect(results.append)
recognizer.language.connect(languages.append)


def load(path: Path):
    audio, sr = sf.read(str(path), dtype="float32")
    assert sr == 16000
    return audio


ru = load(ROOT / ".tmp" / "golos" / "train_003.wav")
en = load(ROOT / ".tmp" / "libri" / "en_0.wav")


def start() -> None:
    recognizer.submit(ru, MODE_AUTO)
    recognizer.submit(en, MODE_AUTO)
    recognizer.submit(ru, MODE_AB)


def finish() -> None:
    print("языки:", languages)
    for item in results:
        print([(s, l, (t or "")[:45], e) for s, l, t, e, _ in item])
    print("получено пачек результатов:", len(results), "| ожидалось 3")
    app.quit()


recognizer.ready.connect(start)
recognizer.preload(["whisper", "gigaam"])
QTimer.singleShot(45000, finish)
app.exec()
