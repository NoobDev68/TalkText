"""Сравнение размеров Whisper: small, medium, large-v3-turbo (и large для отсчёта).

Модели скачиваются с HuggingFace в .tmp/bench, считаются WER/CER и скорость
на русских фразах Golos и английских фразах LibriSpeech.

    python scripts/compare_sizes.py --device cuda --n 20
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import certifi
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from bench import edit_distance, norm, wer  # noqa: E402

BENCH = ROOT / ".tmp" / "bench"
CTX = ssl.create_default_context(cafile=certifi.where())

MODELS = {
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    "large-v3": "Systran/faster-whisper-large-v3",
}

# Уже скачанные приложением модели берём как есть, не качаем заново.
LOCAL = {"turbo": "whisper-large-v3-turbo", "large-v3": "whisper-large-v3"}

RU_DATASET = "bond005/sberdevices_golos_10h_crowd"
EN_DATASET = "openslr/librispeech_asr"


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60, context=CTX) as r:
        return json.load(r)


def http_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300, context=CTX) as r:
        return r.read()


def rows(dataset: str, config: str, split: str, count: int) -> list[dict]:
    url = (
        "https://datasets-server.huggingface.co/rows?dataset="
        f"{urllib.parse.quote(dataset)}&config={config}&split={split}&offset=0&length={count}"
    )
    last: Exception | None = None
    for attempt in range(6):
        try:
            return http_json(url)["rows"]
        except Exception as exc:  # noqa: BLE001 — сервер иногда отдаёт 503
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"не удалось получить примеры {dataset}: {last}")


def load_audio(path: Path) -> np.ndarray:
    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sr))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    return audio


def prepare_dataset(name: str, count: int) -> list[dict]:
    """Скачивает фразы и возвращает [{'audio': np.ndarray, 'ref': str, 'dur': float}]."""
    cache = BENCH / name
    cache.mkdir(parents=True, exist_ok=True)
    audio_cache = cache / "audio"
    audio_cache.mkdir(exist_ok=True)
    index = cache / "index.json"
    if index.exists():
        items = json.loads(index.read_text(encoding="utf-8"))
    else:
        items = []
        needed = count
        fetched = 0
        while needed > 0 and fetched < count * 3:
            chunk = 100 if needed > 20 else max(needed * 2, 20)
            if name == "ru":
                data = rows(RU_DATASET, "default", "train", chunk)
                for row in data:
                    items.append(
                        {"src": row["row"]["audio"][0]["src"], "ref": row["row"]["transcription"]}
                    )
            else:
                data = rows(EN_DATASET, "clean", "test", chunk)
                for row in data:
                    items.append({"src": row["row"]["audio"][0]["src"], "ref": row["row"]["text"]})
            fetched += len(data)
            # для английского берём короткие фразы: длинные не про диктовку
            if name == "en":
                items = [i for i in items if len(i["ref"].split()) <= 25]
            needed = count - len(items)
            if len(data) == 0:
                break
        index.write_text(json.dumps(items[:count], ensure_ascii=False, indent=1), encoding="utf-8")
        items = items[:count]

    prepared = []
    for i, item in enumerate(items[:count]):
        path = audio_cache / f"{i:03d}.flac"
        if not path.exists():
            path.write_bytes(http_bytes(item["src"]))
        audio = load_audio(path)
        prepared.append({"audio": audio, "ref": item["ref"], "dur": len(audio) / 16000})
    print(f"  {name}: {len(prepared)} фраз, {sum(p['dur'] for p in prepared):.0f} с речи", flush=True)
    return prepared


def model_dir(key: str) -> Path:
    """Скачивает все нужные файлы репозитория и возвращает локальную папку."""
    local = ROOT / "models" / LOCAL.get(key, "")
    if key in LOCAL and (local / "model.bin").exists() and (local / "config.json").exists():
        return local
    target = BENCH / "models" / key
    target.mkdir(parents=True, exist_ok=True)
    repo = MODELS[key]
    if (target / "model.bin").exists() and (target / "config.json").exists():
        return target
    info = http_json(f"https://huggingface.co/api/models/{repo}")
    files = [
        s["rfilename"]
        for s in info.get("siblings", [])
        if s["rfilename"] not in ("README.md", ".gitattributes")
    ]
    for name in files:
        dest = target / name
        if dest.exists():
            continue
        print(f"    качаю {key}/{name}", flush=True)
        dest.write_bytes(http_bytes(f"https://huggingface.co/{repo}/resolve/main/{name}"))
    return target


def run(key: str, device: str, sets: list[dict]) -> dict:
    from faster_whisper import WhisperModel

    compute = "float16" if device == "cuda" else "int8"
    folder = model_dir(key)
    print(f"  {key}: загружаю на {device}/{compute}", flush=True)
    started = time.perf_counter()
    model = WhisperModel(str(folder), device=device, compute_type=compute)
    load = time.perf_counter() - started
    # прогрев, чтобы время загрузки не попало в замеры
    model.transcribe(np.zeros(16000, dtype=np.float32), language=None, beam_size=5)

    stats = {}
    for lang, items in sets.items():
        total_wer = total_cer = total_time = total_dur = 0.0
        samples = []
        for item in items:
            t0 = time.perf_counter()
            segments, _info = model.transcribe(
                item["audio"],
                language=lang,
                beam_size=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=False,
                without_timestamps=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            total_time += time.perf_counter() - t0
            ref = norm(item["ref"])
            hyp = norm(text)
            total_wer += wer(ref, hyp)
            total_cer += edit_distance(list(ref), list(hyp)) / max(1, len(ref))
            total_dur += item["dur"]
            if len(samples) < 2:
                samples.append(text)
        n = len(items)
        stats[lang] = {
            "wer": 100 * total_wer / n,
            "cer": 100 * total_cer / n,
            "sec": total_time / n,
            "rtf": total_time / max(total_dur, 1e-6),
            "samples": samples,
        }
    print(f"  {key}: готово (загрузка {load:.1f} с)", flush=True)
    return {"load": load, "sets": stats, "size_mb": folder_size(folder)}


def folder_size(path: Path) -> int:
    return int(sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1048576)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--models", default="small,medium,turbo,large-v3")
    args = parser.parse_args()

    BENCH.mkdir(parents=True, exist_ok=True)
    if args.device == "cuda":
        from app.engines import _add_nvidia_dlls

        _add_nvidia_dlls()  # cuBLAS/cuDNN лежат в vendor/nvidia, как у приложения
    print("готовлю данные", flush=True)
    ru = prepare_dataset("ru", args.n)
    en = prepare_dataset("en", args.n)
    sets = {"ru": ru, "en": en}

    results = {}
    for key in [k for k in args.models.split(",") if k]:
        print(f"\n=== {key} ({MODELS[key]}) ===", flush=True)
        results[key] = run(key, args.device, sets)

    device = args.device
    print(f"\n=== ИТОГО ({device}) ===")
    header = f"{'модель':<12}{'размер':>9} | {'RU WER':>7}{'RU CER':>8}{'RU с/фр':>9} | {'EN WER':>7}{'EN CER':>8}{'EN с/фр':>9}"
    print(header)
    print("-" * len(header))
    for key, res in results.items():
        ru_s, en_s = res["sets"]["ru"], res["sets"]["en"]
        print(
            f"{key:<12}{res['size_mb']:>7} МБ | {ru_s['wer']:>6.1f}%{ru_s['cer']:>7.1f}%{ru_s['sec']:>8.2f} "
            f"| {en_s['wer']:>6.1f}%{en_s['cer']:>7.1f}%{en_s['sec']:>8.2f}"
        )

    print("\n=== примеры распознавания ===")
    for key, res in results.items():
        print(f"\n{key}:")
        print(f"  RU: {res['sets']['ru']['samples'][0][:110]}")
        print(f"  EN: {res['sets']['en']['samples'][0][:110]}")

    out = BENCH / f"results_{device}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nсохранено: {out}")


if __name__ == "__main__":
    main()
