"""Как авто-режим справляется со смешанными русско-английскими фразами."""

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engines import Engines  # noqa: E402
from app.recognizer import MODE_AUTO, Recognizer  # noqa: E402
from app import models  # noqa: E402


def load(path: Path):
    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sr))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    return audio


engines = Engines()
recognizer = Recognizer(engines)
available = models.available_engines()
print("движки:", sorted(available))
base = engines.get("whisper_base")
gigaam = engines.get("gigaam")

for name in ("mix_ru", "mix_en"):
    audio = load(ROOT / ".tmp" / f"{name}.wav")
    lang, cache = recognizer._detect(audio, available)
    plan = recognizer._plan(lang, MODE_AUTO, available)
    print(f"\n=== {name} ===")
    print("  язык:", lang, "| план:", plan)
    for short, language in plan:
        text = cache.get((short, language)) or cache.get((short, None))
        if text is None:
            text = engines.get(short).transcribe(audio, language=language)
        print(f"  AUTO -> {short}: {text}")
    print("  base(None):", base.transcribe(audio, None))
    print("  base(en):  ", base.transcribe(audio, "en"))
    print("  gigaam:    ", gigaam.transcribe(audio))
