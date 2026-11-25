"""Сегментация речи по паузам с помощью Silero VAD.

Работает покадрово (окно 32 мс при 16 кГц) и выдаёт готовые речевые сегменты.
"""

from __future__ import annotations

import numpy as np
from silero_vad_lite import SileroVAD

SAMPLE_RATE = 16_000
FRAME = 512  # 32 мс


class VoiceSegmenter:
    def __init__(
        self,
        *,
        on_threshold: float = 0.5,
        off_threshold: float = 0.35,
        min_silence_frames: int = 20,  # ~0.64 с тишины — конец фразы
        max_segment_frames: int = 900,  # ~29 с — принудительная нарезка
        pre_roll_frames: int = 10,  # ~0.32 с до начала речи
        min_speech_frames: int = 8,  # отбрасываем совсем короткие щелчки
    ) -> None:
        self._vad = SileroVAD(SAMPLE_RATE)
        self.on_threshold = on_threshold
        self.off_threshold = off_threshold
        self.min_silence_frames = min_silence_frames
        self.max_segment_frames = max_segment_frames
        self.pre_roll_frames = pre_roll_frames
        self.min_speech_frames = min_speech_frames
        self._reset()

    def _reset(self) -> None:
        self._pre_roll: list[np.ndarray] = []
        self._frames: list[np.ndarray] = []
        self._speaking = False
        self._silence = 0
        self._speech = 0
        self._level = 0.0

    def reset(self) -> None:
        self._reset()
        self._vad.reset()

    @property
    def level(self) -> float:
        """Текущий уровень сигнала 0..1 (для индикатора)."""
        return self._level

    @property
    def speaking(self) -> bool:
        return self._speaking

    def flush(self) -> np.ndarray | None:
        """Отдаёт недоговорённый сегмент при остановке записи."""
        if self._speaking and self._speech >= self.min_speech_frames and self._frames:
            frames = self._frames
            self._frames = []
            self._speaking = False
            return np.concatenate(frames)
        self._frames = []
        self._speaking = False
        return None

    def feed(self, frame: np.ndarray) -> np.ndarray | None:
        """Скармливает кадр (512 float32). Возвращает готовый сегмент или None."""
        frame = np.ascontiguousarray(frame, dtype=np.float32)
        self._level = float(np.sqrt(np.mean(frame * frame))) * 4.0
        if self._level > 1.0:
            self._level = 1.0
        prob = self._vad.process(memoryview(frame.data))

        if not self._speaking:
            self._pre_roll.append(frame)
            if len(self._pre_roll) > self.pre_roll_frames:
                self._pre_roll.pop(0)
            if prob >= self.on_threshold:
                self._speaking = True
                self._frames = list(self._pre_roll)
                self._pre_roll.clear()
                self._silence = 0
                self._speech = 0
            return None

        self._frames.append(frame)
        self._speech += 1
        if prob >= self.off_threshold:
            self._silence = 0
        else:
            self._silence += 1

        if self._silence >= self.min_silence_frames or len(self._frames) >= self.max_segment_frames:
            frames, speech = self._frames, self._speech
            self._frames = []
            self._speaking = False
            self._silence = 0
            self._speech = 0
            self._vad.reset()
            if speech >= self.min_speech_frames:
                return np.concatenate(frames)
            return None
        return None
