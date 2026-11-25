"""Сравнение движков на русской речи из открытого датасета Golos.

Скачивает N примеров (16 кГц + эталонная транскрипция), прогоняет Whisper и
GigaAM, считает WER/CER и скорость. Только чтение сети и вывод в консоль.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import certifi
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

DATASET = "bond005/sberdevices_golos_10h_crowd"


def http_json(url: str) -> dict:
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=60, context=ctx) as r:
        return json.load(r)


def http_bytes(url: str) -> bytes:
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
        return r.read()


def norm(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def edit_distance(ref: list[str], hyp: list[str]) -> int:
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h)))
        prev = cur
    return prev[-1]


def wer(ref: str, hyp: str) -> float:
    r, h = ref.split(), hyp.split()
    return edit_distance(r, h) / max(1, len(r))


def load_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2, "ожидается 16-бит PCM"
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() > 1:
            data = data.reshape(-1, w.getnchannels()).mean(axis=1).astype(np.int16)
    return data.astype(np.float32) / 32768.0


def fetch_samples(count: int, split: str) -> list[dict]:
    cache = ROOT / ".tmp" / "golos"
    cache.mkdir(parents=True, exist_ok=True)
    index = cache / f"index_{split}_{count}.json"
    if index.exists():
        return json.loads(index.read_text(encoding="utf-8"))

    url = (
        "https://datasets-server.huggingface.co/rows?dataset="
        f"{urllib.parse.quote(DATASET)}&config=default&split={split}&offset=0&length={count}"
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            rows = http_json(url)["rows"]
            break
        except Exception as exc:  # noqa: BLE001 — сервер часто отдаёт 503
            last_error = exc
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"не удалось получить примеры: {last_error}")

    items = [
        {"src": row["row"]["audio"][0]["src"], "ref": row["row"]["transcription"]}
        for row in rows
    ]
    index.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--split", default="train")
    parser.add_argument("--engines", default="whisper,gigaam")
    args = parser.parse_args()

    import sys

    sys.path.insert(0, str(ROOT))
    from app.engines import Engines

    engines = Engines()
    names = [e for e in args.engines.split(",") if e]

    cache = ROOT / ".tmp" / "golos"
    cache.mkdir(parents=True, exist_ok=True)
    items = fetch_samples(args.n, args.split)
    print(f"примеров: {len(items)}")

    for name in names:
        t_load = time.perf_counter()
        engine = engines.get(name)
        print(f"{name}: загружен за {time.perf_counter() - t_load:.1f} с ({getattr(engine, 'device', '?')})")

    stats = {name: {"wer": 0.0, "cer": 0.0, "time": 0.0, "dur": 0.0, "texts": []} for name in names}
    for i, item in enumerate(items):
        wav_path = cache / f"{args.split}_{i:03d}.wav"
        if not wav_path.exists():
            wav_path.write_bytes(http_bytes(item["src"]))
        audio = load_wav(wav_path)
        dur = len(audio) / 16000
        ref = norm(item["ref"])
        line = [f"{i:02d}", f"{dur:4.1f}с", f"ref: {ref[:60]}"]
        for name in names:
            t0 = time.perf_counter()
            hyp = engine_text(engines, name, audio)
            dt = time.perf_counter() - t0
            st = stats[name]
            st["wer"] += wer(ref, norm(hyp))
            st["cer"] += edit_distance(list(ref), list(norm(hyp))) / max(1, len(ref))
            st["time"] += dt
            st["dur"] += dur
            st["texts"].append((ref, norm(hyp)))
            line.append(f"{name}: {hyp[:50]}")
        print(" | ".join(line))

    print("\n=== ИТОГО ===")
    for name in names:
        st = stats[name]
        n = len(items)
        rtf = st["time"] / max(st["dur"], 1e-6)
        print(
            f"{name}: WER {100 * st['wer'] / n:.1f}% | CER {100 * st['cer'] / n:.1f}% | "
            f"скорость {st['time'] / n:.2f} с/фразу (x{rtf:.2f} от длины)"
        )


def engine_text(engines, name: str, audio) -> str:
    return engines.get(name).transcribe(audio)


if __name__ == "__main__":
    main()
