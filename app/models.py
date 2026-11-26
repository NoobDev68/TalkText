"""Реестр движков-моделей: что можно скачать, проверка установки, загрузка.

Модели качаются с HuggingFace, CUDA-библиотеки — с PyPI (нужны только Whisper).
"""

from __future__ import annotations

import os
import shutil
import ssl
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import certifi

from . import paths

ROOT = paths.APP_DIR
MODELS_DIR = paths.MODELS_DIR
VENDOR = paths.VENDOR_DIR

_CTX = ssl.create_default_context(cafile=certifi.where())

# Wheel-ы NVIDIA для GPU-режима Whisper: имя пакета -> версия.
_CUDA_PACKAGES = {
    "nvidia-cublas-cu12": "12.9.2.10",
    "nvidia-cudnn-cu12": "9.28.1.4",
    "nvidia-cuda-runtime-cu12": "12.9.79",
}


class Cancelled(Exception):
    """Скачивание прервано пользователем."""


# Движки, которым нужны CUDA-библиотеки (общий пакет vendor/nvidia).
_GPU_KEYS = ("whisper", "whisper_turbo")


@dataclass(frozen=True)
class ModelSpec:
    key: str
    size_mb: int
    kind: str  # "hf" | "cuda"
    repo: str = ""
    target: str = ""
    files: tuple[str, ...] = ()
    marker: str = ""
    requires: tuple[str, ...] = ()
    shown: bool = True


MODELS: dict[str, ModelSpec] = {
    "gigaam": ModelSpec(
        key="gigaam",
        size_mb=216,
        kind="hf",
        repo="istupakov/gigaam-v3-onnx",
        target="gigaam-v3",
        files=(
            "config.json",
            "v3_e2e_rnnt_vocab.txt",
            "v3_e2e_rnnt_encoder.int8.onnx",
            "v3_e2e_rnnt_decoder.int8.onnx",
            "v3_e2e_rnnt_joint.int8.onnx",
        ),
        marker="v3_e2e_rnnt_encoder.int8.onnx",
    ),
    "gigaam_ml": ModelSpec(
        key="gigaam_ml",
        size_mb=214,
        kind="hf",
        repo="istupakov/gigaam-multilingual-ctc-onnx",
        target="gigaam-multilingual",
        files=("config.json", "multilingual_vocab.txt", "multilingual_ctc.int8.onnx"),
        marker="multilingual_ctc.int8.onnx",
    ),
    "whisper_ru": ModelSpec(
        key="whisper_ru",
        size_mb=1543,
        kind="hf",
        repo="bond005/whisper-podlodka-turbo-ct2",
        target="whisper-podlodka-turbo",
        files=(
            "config.json",
            "model.bin",
            "preprocessor_config.json",
            "tokenizer.json",
            "vocabulary.json",
        ),
        marker="model.bin",
        requires=("cuda",),
    ),
    "whisper_small": ModelSpec(
        key="whisper_small",
        size_mb=463,
        kind="hf",
        repo="Systran/faster-whisper-small",
        target="whisper-small",
        files=(
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.txt",
        ),
        marker="model.bin",
    ),
    "whisper_base": ModelSpec(
        key="whisper_base",
        size_mb=102,
        kind="hf",
        repo="istupakov/whisper-base-onnx",
        target="whisper-base",
        files=(
            "config.json",
            "whisper-base_beamsearch.int8.onnx",
            "vocab.json",
            "added_tokens.json",
        ),
        marker="whisper-base_beamsearch.int8.onnx",
    ),
    # Whisper large-v3 больше не предлагается: turbo даёт то же качество и вдвое
    # быстрее. Спека осталась, чтобы корректно работать с уже скачанными копиями.
    "whisper": ModelSpec(
        key="whisper",
        size_mb=4728,
        kind="hf",
        repo="Systran/faster-whisper-large-v3",
        target="whisper-large-v3",
        files=(
            "config.json",
            "model.bin",
            "preprocessor_config.json",
            "tokenizer.json",
            "vocabulary.json",
        ),
        marker="model.bin",
        requires=("cuda",),
        shown=False,
    ),
    "whisper_turbo": ModelSpec(
        key="whisper_turbo",
        size_mb=1543,
        kind="hf",
        repo="deepdml/faster-whisper-large-v3-turbo-ct2",
        target="whisper-large-v3-turbo",
        files=(
            "config.json",
            "model.bin",
            "preprocessor_config.json",
            "tokenizer.json",
            "vocabulary.json",
        ),
        marker="model.bin",
        requires=("cuda",),
    ),
    "cuda": ModelSpec(
        key="cuda",
        size_mb=1782,
        kind="cuda",
        marker="cublas64_12.dll",
        shown=False,
    ),
}


def _files_dir(spec: ModelSpec) -> Path:
    if spec.kind == "cuda":
        return VENDOR / "nvidia"
    return MODELS_DIR / spec.target


def installed(key: str) -> bool:
    spec = MODELS[key]
    if spec.kind == "cuda":
        return (VENDOR / "nvidia" / "cublas" / "bin" / spec.marker).is_file()
    return (_files_dir(spec) / spec.marker).is_file()


def installed_keys() -> set[str]:
    return {key for key in MODELS if installed(key)}


# Движки, которые вообще бывают в работе (cuda сама по себе движком не является).
# Whisper large-v3 снят с поддержки: его место занял turbo с тем же качеством.
ENGINE_KEYS = ("gigaam", "gigaam_ml", "whisper_ru", "whisper_turbo", "whisper_small", "whisper_base")


def enabled_keys() -> set[str]:
    """Движки, выбранные галочками в настройках.

    Снятая галочка движок не удаляет — он просто перестаёт предлагаться в окне.
    Удаление — только кнопкой «Удалить». Если настройки ещё нет, включено всё
    скачанное (поведение старых версий).
    """
    from .settings import app_settings

    raw = app_settings().value("enabled")
    if raw is None:
        # Настройки старого формата: считаем включённым всё скачанное.
        return installed_keys()
    # Пустая строка — пользователь снял все галочки, это осознанный выбор.
    return {key for key in str(raw).split(",") if key in MODELS}


def set_enabled_keys(keys: set[str]) -> None:
    from .settings import app_settings

    settings = app_settings()
    settings.setValue("enabled", ",".join(sorted(keys)))
    settings.sync()


def available_engines() -> set[str]:
    """Движки, которые можно использовать: скачаны и включены галочкой."""
    return {key for key in installed_keys() & enabled_keys() if key in ENGINE_KEYS}


def disk_usage_mb(key: str) -> int:
    path = _files_dir(MODELS[key])
    if not path.exists():
        return 0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return int(total / 1048576)


# --- скачивание ---------------------------------------------------------------


def _download(url: str, dest: Path, on_bytes, cancel=None) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    start = tmp.stat().st_size if tmp.exists() else 0
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-"} if start else {})
    with urllib.request.urlopen(req, timeout=120, context=_CTX) as resp:
        total = start + int(resp.headers.get("Content-Length") or 0)
        mode = "ab" if start and resp.status == 206 else "wb"
        if mode == "wb":
            start = 0
        done = start
        last = 0.0
        with open(tmp, mode) as f:
            while chunk := resp.read(1 << 20):
                if cancel is not None and cancel.is_set():
                    raise Cancelled("скачивание отменено")
                f.write(chunk)
                done += len(chunk)
                now = time.time()
                if now - last > 0.4:
                    last = now
                    on_bytes(done, total)
    if total and done != total:
        raise RuntimeError(f"соединение оборвалось: получено {done} из {total} байт")
    tmp.replace(dest)


def _install_hf(spec: ModelSpec, progress, cancel=None) -> None:
    target = _files_dir(spec)
    target.mkdir(parents=True, exist_ok=True)
    known = {f["name"]: f["size"] for f in _hf_sizes(spec.repo) if f["name"] in spec.files}
    total = sum(known.values()) or 1
    done_before = sum(
        (target / name).stat().st_size for name in spec.files if (target / name).is_file()
    )
    done_before = min(done_before, total)
    for name in spec.files:
        if cancel is not None and cancel.is_set():
            raise Cancelled("скачивание отменено")
        dest = target / name
        if dest.is_file():
            continue
        progress(spec.key, done_before, total)

        def on_bytes(done: int, _file_total: int, base=done_before) -> None:
            progress(spec.key, base + done, total)

        _download(f"https://huggingface.co/{spec.repo}/resolve/main/{name}", dest, on_bytes, cancel)
        done_before += dest.stat().st_size


def _hf_sizes(repo: str) -> list[dict]:
    import json

    url = f"https://huggingface.co/api/models/{repo}?blobs=true"
    with urllib.request.urlopen(url, timeout=30, context=_CTX) as r:
        data = json.load(r)
    return [
        {"name": s["rfilename"], "size": s.get("size") or 0}
        for s in data.get("siblings", [])
        if s.get("size")
    ]


def _cuda_wheel_url(package: str, version: str) -> tuple[str, int]:
    import json

    url = f"https://pypi.org/pypi/{package}/{version}/json"
    with urllib.request.urlopen(url, timeout=60, context=_CTX) as r:
        data = json.load(r)
    for file in data["urls"]:
        if "win_amd64" in file["filename"]:
            return file["url"], file["size"]
    raise RuntimeError(f"нет Windows-сборки {package} {version}")


def _install_cuda(spec: ModelSpec, progress, cancel=None) -> None:
    wheels: list[tuple[str, str, int]] = []
    for package, version in _CUDA_PACKAGES.items():
        url, size = _cuda_wheel_url(package, version)
        wheels.append((package, url, size))
    total = sum(size for _, _, size in wheels)
    done_total = 0
    VENDOR.mkdir(parents=True, exist_ok=True)
    for package, url, size in wheels:
        if cancel is not None and cancel.is_set():
            raise Cancelled("скачивание отменено")
        wheel = MODELS_DIR / f"{package}-{_CUDA_PACKAGES[package]}-win_amd64.whl"
        if not wheel.is_file():
            base = done_total

            def on_bytes(done: int, _total: int, base=base) -> None:
                progress(spec.key, base + done, total)

            _download(url, wheel, on_bytes, cancel)
        if not zipfile.is_zipfile(wheel):
            # Недокачанный или повреждённый файл — начинаем заново.
            wheel.unlink(missing_ok=True)
            base = done_total

            def on_retry(done: int, _total: int, base=base) -> None:
                progress(spec.key, base + done, total)

            _download(url, wheel, on_retry, cancel)
        with zipfile.ZipFile(wheel) as z:
            z.extractall(VENDOR)
        done_total += size
    for wheel in MODELS_DIR.glob("nvidia-*.whl"):
        wheel.unlink(missing_ok=True)


def install(key: str, progress, cancel=None) -> None:
    """Скачивает модель (и её зависимости). progress(key, done_bytes, total_bytes).

    cancel — threading.Event: если установлен, скачивание прерывается исключением
    Cancelled, а недокачанные файлы остаются в *.part для продолжения позже.
    """
    spec = MODELS[key]
    if cancel is not None and cancel.is_set():
        raise Cancelled("скачивание отменено")
    for req in spec.requires:
        if not installed(req):
            install(req, progress, cancel)
    if installed(key):
        return
    if spec.kind == "cuda":
        _install_cuda(spec, progress, cancel)
    else:
        _install_hf(spec, progress, cancel)


def uninstall(key: str) -> None:
    spec = MODELS[key]
    # CUDA-библиотеки общие для GPU-движков: убираем, только если больше никто их не использует.
    if key in _GPU_KEYS and not any(installed(other) for other in _GPU_KEYS if other != key):
        uninstall("cuda")
    shutil.rmtree(_files_dir(spec), ignore_errors=True)
    from .settings import app_settings

    settings = app_settings()
    raw = settings.value("enabled")
    if raw is not None and str(raw):
        left = {item for item in str(raw).split(",") if item and item != key}
        settings.setValue("enabled", ",".join(sorted(left)))
        settings.sync()


def describe() -> list[ModelSpec]:
    # Порядок карточек в настройках.
    order = [
        "gigaam",
        "whisper_ru",
        "whisper_turbo",
        "whisper_small",
        "whisper_base",
        "gigaam_ml",
    ]
    return [MODELS[key] for key in order if MODELS[key].shown]
