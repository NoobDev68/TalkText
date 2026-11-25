"""Сравнение Whisper base и large на сложных английских фразах."""

import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engines import Engines  # noqa: E402

PHRASES = {
    "hard1 (акцент)": ".tmp/hard1.wav",
    "hard2 (имена)": ".tmp/hard2.wav",
    "hard3 (термины)": ".tmp/hard3.wav",
    "en_test (простая)": ".tmp/en_test.wav",
    "libri (литература)": ".tmp/libri/en_0.wav",
}


def load(path: str):
    audio, sr = sf.read(str(ROOT / path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sr))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    return audio


engines = Engines()
base = engines.get("whisper_base")
large = engines.get("whisper")
print("large device:", large.device)

for name, path in PHRASES.items():
    audio = load(path)
    t0 = time.time()
    base_text = base.transcribe(audio, "en")
    base_dt = time.time() - t0
    t0 = time.time()
    large_text = large.transcribe(audio, "en")
    large_dt = time.time() - t0
    print(f"\n== {name}")
    print(f"  base  ({base_dt:.2f}с): {base_text}")
    print(f"  large ({large_dt:.2f}с): {large_text}")
