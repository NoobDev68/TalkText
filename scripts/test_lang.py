"""Проверка многоязычности: GigaAM Multilingual, GigaAM v3 и Whisper на ru/en."""

from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import certifi
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def http_json(url: str) -> dict:
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=60, context=ctx) as r:
        return json.load(r)


def http_bytes(url: str) -> bytes:
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
        return r.read()


def load_wav(path: Path) -> np.ndarray:
    import soundfile as sf

    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        x = np.linspace(0, len(data) - 1, int(len(data) * 16000 / sr))
        data = np.interp(x, np.arange(len(data)), data).astype(np.float32)
    return data.astype(np.float32)


def english_samples(n: int = 3) -> list[tuple[np.ndarray, str]]:
    cache = ROOT / ".tmp" / "libri"
    cache.mkdir(parents=True, exist_ok=True)
    url = (
        "https://datasets-server.huggingface.co/rows?dataset="
        "hf-internal-testing%2Flibrispeech_asr_dummy&config=clean&split=validation&offset=0&length="
        f"{n}"
    )
    out = []
    for i, row in enumerate(http_json(url)["rows"]):
        src = row["row"]["audio"][0]["src"]
        path = cache / f"en_{i}.wav"
        if not path.exists():
            path.write_bytes(http_bytes(src))
        out.append((load_wav(path), row["row"]["text"]))
    return out


def russian_samples(n: int = 3) -> list[tuple[np.ndarray, str]]:
    index = ROOT / ".tmp" / "golos" / "index_train_20.json"
    items = json.loads(index.read_text(encoding="utf-8"))[:n]
    out = []
    for i, item in enumerate(items):
        path = ROOT / ".tmp" / "golos" / f"train_{i:03d}.wav"
        out.append((load_wav(path), item["ref"]))
    return out


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from app.engines import _add_nvidia_dlls

    _add_nvidia_dlls()  # подключает vendor/ (onnx-asr) и DLL NVIDIA

    from faster_whisper import WhisperModel
    from onnx_asr.loader import load_model

    print("загружаю модели…")
    ml = load_model(
        "istupakov/gigaam-multilingual-ctc-onnx",
        path=str(ROOT / "models" / "gigaam-multilingual"),
        quantization="int8",
        providers=["CPUExecutionProvider"],
    )
    v3 = load_model(
        "gigaam-v3-e2e-rnnt",
        path=str(ROOT / "models" / "gigaam-v3"),
        quantization="int8",
        providers=["CPUExecutionProvider"],
    )
    whisper = WhisperModel(str(ROOT / "models" / "whisper-large-v3"), device="cuda", compute_type="float16")

    print("\n=== АНГЛИЙСКИЙ ===")
    for audio, ref in english_samples():
        lang, prob, _ = whisper.detect_language(audio)
        t0 = time.time()
        ml_text = ml.recognize(audio)
        ml_dt = time.time() - t0
        v3_text = v3.recognize(audio)
        ws_text = " ".join(s.text for s in whisper.transcribe(audio, language=None, beam_size=5)[0])
        print(f"ref: {ref[:70]}")
        print(f"  detect: {lang} {prob:.2f}")
        print(f"  ML ({ml_dt:.2f}с): {ml_text[:90]}")
        print(f"  v3(ru): {v3_text[:70]}")
        print(f"  whisper: {ws_text[:90]}")

    print("\n=== РУССКИЙ ===")
    for audio, ref in russian_samples():
        lang, prob, _ = whisper.detect_language(audio)
        ml_text = ml.recognize(audio)
        ws_text = " ".join(s.text for s in whisper.transcribe(audio, language=None, beam_size=5)[0])
        print(f"ref: {ref[:70]}")
        print(f"  detect: {lang} {prob:.2f}")
        print(f"  ML: {ml_text[:90]}")
        print(f"  whisper: {ws_text[:90]}")


if __name__ == "__main__":
    main()
