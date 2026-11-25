"""Движки распознавания речи: faster-whisper (CUDA) и GigaAM v3 (ONNX)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np

from . import paths

ROOT = paths.APP_DIR

# onnx-asr лежит в бандле (vendor), CUDA-библиотеки скачиваются рядом с exe.
_VENDOR = paths.BUNDLED_VENDOR
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

_DLL_DIRS: list = []


def _add_nvidia_dlls() -> None:
    # ctranslate2 грузит cuBLAS/cuDNN по имени, поэтому добавляем каталоги и в PATH:
    # add_dll_directory действует только для LoadLibraryEx с флагом USER_DIRS.
    paths_list = []
    for sub in ("cuda_runtime", "cublas", "cudnn"):
        path = paths.VENDOR_DIR / "nvidia" / sub / "bin"
        if path.is_dir():
            paths_list.append(str(path))
            try:
                _DLL_DIRS.append(os.add_dll_directory(str(path)))
            except OSError:
                pass
    if paths_list:
        os.environ["PATH"] = os.pathsep.join(paths_list + [os.environ.get("PATH", "")])


class EngineError(RuntimeError):
    """Движок недоступен (нет модели, нет GPU и т.п.)."""


# Фразы, которыми Whisper заполняет тишину вместо распознавания.
_HALLUCINATIONS = re.compile(
    r"(продолжение следует|субтитры|редактор субтитров|сделано в|спасибо за просмотр|"
    r"подписывайтесь на канал|до новых встреч)",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    return " ".join(text.split())


class WhisperEngine:
    """OpenAI Whisper large-v3 через faster-whisper, на GPU."""

    name = "Whisper large-v3"
    short = "whisper"

    def __init__(self) -> None:
        _add_nvidia_dlls()
        model_dir = ROOT / "models" / "whisper-large-v3"
        if not (model_dir / "model.bin").is_file():
            raise EngineError("не найдена модель models/whisper-large-v3 (запустите scripts/download_models.py whisper)")
        self._model_dir = str(model_dir)
        try:
            self._load("cuda", "float16")
        except Exception:  # нет GPU, не загрузились DLL — считаем на CPU
            self._load("cpu", "int8")

    def _load(self, device: str, compute_type: str) -> None:
        from faster_whisper import WhisperModel

        self._model = WhisperModel(self._model_dir, device=device, compute_type=compute_type)
        self.device = "GPU" if device == "cuda" else "CPU"
        self._run(np.zeros(16000, dtype=np.float32), "ru")

    def _run(self, audio, language: str | None) -> str:
        segments, _info = self._model.transcribe(
            audio,
            language=language,
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
            without_timestamps=True,
        )
        parts = []
        for seg in segments:
            text = seg.text.strip()
            # Whisper «додумывает» тишину и шум: выкидываем такие сегменты.
            if not text or seg.no_speech_prob > 0.6 and seg.avg_logprob < -0.4:
                continue
            if _HALLUCINATIONS.fullmatch(text.rstrip(".")):
                continue
            parts.append(text)
        return _clean(" ".join(parts))

    def transcribe(self, audio, language: str | None = None) -> str:
        try:
            return self._run(audio, language)
        except RuntimeError as exc:
            # DLL NVIDIA пропали или не грузятся — досчитываем на CPU, а не падаем.
            if self.device == "GPU" and "dll" in str(exc).lower():
                self._load("cpu", "int8")
                return self._run(audio, language)
            raise

    def detect_language(self, audio) -> tuple[str, float]:
        language, probability, _all = self._model.detect_language(audio)
        return language, probability


class GigaamEngine:
    """GigaAM v3 E2E RNNT (пунктуация и нормализация чисел) через onnx-asr."""

    name = "GigaAM v3"
    short = "gigaam"

    def __init__(self) -> None:
        model_dir = ROOT / "models" / "gigaam-v3"
        if not (model_dir / "v3_e2e_rnnt_encoder.int8.onnx").is_file():
            raise EngineError("не найдена модель models/gigaam-v3 (запустите scripts/download_models.py gigaam)")
        import onnx_asr

        self._model = onnx_asr.load_model(
            "gigaam-v3-e2e-rnnt",
            path=str(model_dir),
            quantization="int8",
            providers=["CPUExecutionProvider"],
        )
        self.device = "CPU"
        self._model.recognize(np.zeros(16000, dtype=np.float32))

    def transcribe(self, audio, language: str | None = "ru") -> str:
        return _clean(self._model.recognize(audio))


class GigaamMultilingualEngine:
    """GigaAM Multilingual CTC (ru/en) — быстрый многоязычный вариант без пунктуации."""
    name = "GigaAM Multilingual"
    short = "gigaam_ml"

    def __init__(self) -> None:
        model_dir = ROOT / "models" / "gigaam-multilingual"
        if not (model_dir / "multilingual_ctc.int8.onnx").is_file():
            raise EngineError(
                "не найдена модель models/gigaam-multilingual "
                "(запустите scripts/download_models.py gigaam-ml)"
            )
        import onnx_asr

        self._model = onnx_asr.load_model(
            "istupakov/gigaam-multilingual-ctc-onnx",
            path=str(model_dir),
            quantization="int8",
            providers=["CPUExecutionProvider"],
        )
        self.device = "CPU"
        self._model.recognize(np.zeros(16000, dtype=np.float32))

    def transcribe(self, audio, language: str | None = None) -> str:
        return _clean(self._model.recognize(audio))


class WhisperBaseEngine:
    """Whisper base (ONNX int8, процессор) — лёгкий английский с пунктуацией."""

    name = "Whisper base"
    short = "whisper_base"

    def __init__(self) -> None:
        model_dir = ROOT / "models" / "whisper-base"
        if not (model_dir / "whisper-base_beamsearch.int8.onnx").is_file():
            raise EngineError(
                "не найдена модель models/whisper-base "
                "(запустите scripts/download_models.py whisper_base)"
            )
        import onnx_asr

        self._model = onnx_asr.load_model(
            "whisper-base",
            path=str(model_dir),
            quantization="int8",
            providers=["CPUExecutionProvider"],
        )
        self.device = "CPU"
        self._model.recognize(np.zeros(16000, dtype=np.float32), language="en")

    def transcribe(self, audio, language: str | None = None) -> str:
        return _clean(self._model.recognize(audio, language=language))


class Engines:
    """Ленивая загрузка движков: грузим только то, что реально используется."""

    def __init__(self) -> None:
        self._instances: dict[str, object] = {}
        self._errors: dict[str, str] = {}

    def get(self, short: str):
        if short in self._instances:
            return self._instances[short]
        if short in self._errors:
            raise EngineError(self._errors[short])
        cls = {
            "whisper": WhisperEngine,
            "whisper_base": WhisperBaseEngine,
            "gigaam": GigaamEngine,
            "gigaam_ml": GigaamMultilingualEngine,
        }[short]
        try:
            engine = cls()
        except Exception as exc:  # noqa: BLE001 — любая причина делает движок недоступным
            message = str(exc) if isinstance(exc, EngineError) else f"{type(exc).__name__}: {exc}"
            self._errors[short] = message
            raise EngineError(message) from exc
        self._instances[short] = engine
        return engine

    def preload(self, shorts: list[str]) -> None:
        for short in shorts:
            try:
                self.get(short)
            except Exception:  # noqa: BLE001
                pass
