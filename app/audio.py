"""Захват микрофона и VAD-сегментация в фоне."""

from __future__ import annotations

import queue
import threading

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from .segmenter import FRAME, SAMPLE_RATE, VoiceSegmenter


class Recorder(QObject):
    segment_ready = Signal(object)  # np.float32 [N]
    level_changed = Signal(float)
    speaking_changed = Signal(bool)
    error = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._stream: sd.InputStream | None = None
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False
        self._seg: VoiceSegmenter | None = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._seg = VoiceSegmenter()
        self._queue = queue.Queue()
        self._running = True
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=FRAME,
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:  # нет микрофона / занят
            self._running = False
            self._stream = None
            self.error.emit(f"Микрофон недоступен: {exc}")
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._seg is not None:
            tail = self._seg.flush()
            if tail is not None:
                self.segment_ready.emit(tail)

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            pass
        self._queue.put(indata[:, 0].copy())

    def _loop(self) -> None:
        seg = self._seg
        assert seg is not None
        while self._running:
            try:
                frame = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                result = seg.feed(frame)
            except Exception as exc:
                self.error.emit(f"Ошибка VAD: {exc}")
                continue
            self.level_changed.emit(seg.level)
            self.speaking_changed.emit(seg.speaking)
            if result is not None:
                self.segment_ready.emit(result)
