from __future__ import annotations

import queue
import threading
import math
from collections import deque
from collections.abc import Callable

import numpy as np
import sounddevice as sd

from .config import Settings


class PhraseRecorder:
    """Groups microphone blocks into phrases using a lightweight energy gate."""

    def __init__(self, settings: Settings, on_phrase: Callable[[np.ndarray], None]) -> None:
        self.settings = settings
        self.on_phrase = on_phrase
        self._blocks: queue.Queue[np.ndarray] = queue.Queue(maxsize=100)
        self._stop = threading.Event()

    @staticmethod
    def list_devices() -> None:
        print(sd.query_devices())

    def _callback(self, indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags) -> None:
        if status:
            print(f"Audio warning: {status}")
        try:
            self._blocks.put_nowait(indata[:, 0].copy())
        except queue.Full:
            pass

    def run(self) -> None:
        block_frames = self.settings.sample_rate * self.settings.block_ms // 1000
        silence_blocks = max(1, math.ceil(self.settings.silence_ms / self.settings.block_ms))
        min_blocks = max(1, math.ceil(self.settings.min_speech_ms / self.settings.block_ms))
        max_blocks = max(1, math.ceil(self.settings.max_phrase_ms / self.settings.block_ms))
        phrase: list[np.ndarray] = []
        pre_roll: deque[np.ndarray] = deque(maxlen=2)
        quiet = 0
        voiced_blocks = 0
        speaking = False

        with sd.InputStream(
            device=self.settings.normalized_input_device(),
            channels=1,
            samplerate=self.settings.sample_rate,
            blocksize=block_frames,
            dtype="float32",
            callback=self._callback,
        ):
            print("Listening for Spanish speech...")
            while not self._stop.is_set():
                try:
                    block = self._blocks.get(timeout=0.2)
                except queue.Empty:
                    continue

                rms = float(np.sqrt(np.mean(np.square(block))))
                is_voice = rms >= self.settings.speech_threshold

                if not speaking:
                    pre_roll.append(block)
                    if not is_voice:
                        continue
                    speaking = True
                    phrase = list(pre_roll)
                    pre_roll.clear()
                    voiced_blocks = 1
                    quiet = 0
                    continue

                phrase.append(block)
                if is_voice:
                    voiced_blocks += 1
                    quiet = 0
                else:
                    quiet += 1

                finished = phrase and (quiet >= silence_blocks or len(phrase) >= max_blocks)
                if finished:
                    if voiced_blocks >= min_blocks:
                        self.on_phrase(np.concatenate(phrase))
                    phrase = []
                    quiet = 0
                    voiced_blocks = 0
                    speaking = False

    def stop(self) -> None:
        self._stop.set()
