"""Фоновое распознавание: очередь сегментов, выбор языка и движка."""

from __future__ import annotations

import queue
import threading
import time

from PySide6.QtCore import QObject, Signal

from . import models
from .engines import EngineError, Engines

# Режимы работы окна.
MODE_AUTO = "auto"  # язык определяется автоматически
MODE_RU = "ru"  # принудительно русский
MODE_EN = "en"  # принудительно английский

LANGUAGE_NAMES = {"ru": "RU", "en": "EN"}


def guess_language(text: str) -> str:
    """Язык по алфавиту расшифровки: кириллица -> русский, латиница -> английский.

    В смешанной фразе нескольких кириллических слов достаточно, чтобы считать
    речь русской: иначе «Включи YouTube и скажи test» ушла бы в английский
    движок, а тот переводит русскую часть вместо распознавания.
    """
    cyrillic = sum(1 for ch in text if "\u0400" <= ch <= "\u04ff")
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cyrillic == 0 and latin == 0:
        return ""
    if cyrillic == 0:
        return "en"
    if latin == 0:
        return "ru"
    return "ru" if cyrillic >= latin * 0.15 else "en"


class Recognizer(QObject):
    results = Signal(list)  # [(short, lang, text | None, error | None, elapsed)]
    language = Signal(str)  # определённый язык ("" — не определялся)
    ready = Signal()
    error = Signal(str)

    def __init__(self, engines: Engines, parent=None) -> None:
        super().__init__(parent)
        self._engines = engines
        self._queue: queue.Queue = queue.Queue()
        self._last_lang: str | None = None
        threading.Thread(target=self._loop, daemon=True).start()

    def preload(self, shorts: list[str]) -> None:
        self._queue.put(("preload", shorts))

    def submit(self, audio, mode: str, engine: str = "") -> None:
        self._queue.put(("recognize", audio, mode, engine))

    def _loop(self) -> None:
        while True:
            task = self._queue.get()
            if task[0] == "preload":
                for short in task[1]:
                    try:
                        self._engines.get(short)
                    except EngineError as exc:
                        self.error.emit(str(exc))
                self.ready.emit()
                continue

            _, audio, mode, engine = task
            available = models.available_engines()
            if not available:
                self.results.emit([("", "", None, "Не установлен ни один движок. Откройте настройки.", 0.0)])
                continue

            try:
                if engine and engine in available:
                    # Движок выбран вручную: язык берём из режима окна, а Whisper
                    # и Multilingual с «Авто» определяют его сами — без отдельного шага.
                    lang = {"ru": "ru", "en": "en"}.get(mode, "")
                    if lang:
                        self.language.emit(lang)
                    cache: dict[tuple[str, str | None], str] = {}
                    plan = [(engine, None if engine in ("gigaam", "gigaam_ml") else lang or None)]
                elif mode != MODE_AUTO:
                    # Язык задан кнопкой — определять его по фразе незачем: экономим проход.
                    cache = {}
                    plan = self._plan("", mode, available)
                else:
                    lang, cache = self._detect(audio, available)
                    plan = self._plan(lang, mode, available)
            except EngineError as exc:
                self.results.emit([("", "", None, str(exc), 0.0)])
                continue

            if not plan:
                self.results.emit([("", "", None, "Для этого режима нет установленного движка", 0.0)])
                continue

            out = []
            for short, language in plan:
                t0 = time.perf_counter()
                try:
                    cached = cache.get((short, language))
                    if cached is None:
                        cached = cache.get((short, None))
                    if cached is not None:
                        text = cached
                    else:
                        text = self._engines.get(short).transcribe(audio, language=language)
                    out.append((short, language, text, None, time.perf_counter() - t0))
                except EngineError as exc:
                    out.append((short, language, None, str(exc), time.perf_counter() - t0))
                except Exception as exc:  # noqa: BLE001
                    out.append((short, language, None, f"ошибка: {exc}", time.perf_counter() - t0))
            self.results.emit(out)

    def _detect(self, audio, available: set[str]) -> tuple[str, dict[tuple[str, str | None], str]]:
        """Язык сегмента и кэш уже готовых расшифровок (Multilingual считаем один раз)."""
        cache: dict[tuple[str, str | None], str] = {}

        if available & {"whisper_turbo", "whisper_ru", "whisper_small"}:
            for key in ("whisper_turbo", "whisper_ru", "whisper_small"):
                if key not in available:
                    continue
                try:
                    lang, prob = self._engines.get(key).detect_language(audio)
                except EngineError:
                    continue
                if prob >= 0.6 and lang in ("ru", "en"):
                    self._last_lang = lang
                    self.language.emit(lang)
                    return lang, cache
                if prob >= 0.6:
                    return "", cache

        # Whisper base определяет язык по первым словам лучше, чем алфавит Multilingual:
        # на смешанных фразах Multilingual часто уходит в кириллицу.
        if "whisper_base" in available:
            text = self._engines.get("whisper_base").transcribe(audio, language=None)
            cache[("whisper_base", None)] = text
            lang = guess_language(text)
            if lang:
                self._last_lang = lang
                self.language.emit(lang)
            return lang, cache

        if "gigaam_ml" in available:
            text = self._engines.get("gigaam_ml").transcribe(audio, language=None)
            cache[("gigaam_ml", None)] = text
            lang = guess_language(text)
            if lang:
                self._last_lang = lang
                self.language.emit(lang)
            return lang, cache

        # Язык так и не определился: если есть Whisper с автоопределением — пусть решает
        # сам (для «Авто» это лучше, чем насильно считать фразу русской).
        if available & {"whisper_turbo", "whisper_ru", "whisper_small"}:
            return "", cache
        return "ru", cache

    def _plan(self, lang: str, mode: str, available: set[str]) -> list[tuple[str, str | None]]:
        """Какие движки и с каким языком запускать для этого сегмента."""
        if mode == MODE_RU:
            self.language.emit("ru")
            return self._for_language("ru", available)
        if mode == MODE_EN:
            self.language.emit("en")
            return self._for_language("en", available)

        if lang in ("ru", "en"):
            return self._for_language(lang, available)
        # Другой язык или неуверенность — Whisper автоопределение, иначе лёгкий Whisper / Multilingual.
        if "whisper_turbo" in available:
            return [("whisper_turbo", None)]
        if "whisper_ru" in available:
            return [("whisper_ru", None)]

        if "whisper_small" in available:
            return [("whisper_small", None)]
        if "whisper_base" in available:
            return [("whisper_base", None)]
        if "gigaam_ml" in available:
            return [("gigaam_ml", None)]
        return []

    @staticmethod
    def _for_language(lang: str, available: set[str]) -> list[tuple[str, str | None]]:
        if lang == "ru":
            # GigaAM v3 — самый устойчивый к шуму и всегда ставит пунктуацию.
            # Podlodka turbo точнее на чистой речи и быстрее на видеокарте.
            if "gigaam" in available:
                return [("gigaam", "ru")]
            if "whisper_ru" in available:
                return [("whisper_ru", "ru")]
            if "gigaam_ml" in available:
                return [("gigaam_ml", None)]

            if "whisper_turbo" in available:
                return [("whisper_turbo", "ru")]
            if "whisper_small" in available:
                return [("whisper_small", "ru")]
            if "whisper_base" in available:
                return [("whisper_base", "ru")]
            return []
        # Английский: turbo — то же качество, что у large, но вдвое быстрее.
        if "whisper_turbo" in available:
            return [("whisper_turbo", "en")]
        if "whisper_ru" in available:
            return [("whisper_ru", "en")]

        if "whisper_small" in available:
            return [("whisper_small", "en")]
        if "whisper_base" in available:
            return [("whisper_base", "en")]
        if "gigaam_ml" in available:
            return [("gigaam_ml", None)]
        return []
