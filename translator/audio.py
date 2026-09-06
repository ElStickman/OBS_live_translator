from __future__ import annotations

import math
import queue
import threading
from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager

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

    def _queue_block(self, block: np.ndarray) -> None:
        if block.ndim == 2:
            block = np.mean(block, axis=1)
        try:
            self._blocks.put_nowait(block.astype(np.float32, copy=True))
        except queue.Full:
            pass

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            print(f"Audio warning: {status}")
        self._queue_block(indata)

    @staticmethod
    def _resample(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
        if source_rate == target_rate or audio.size == 0:
            return audio.astype(np.float32, copy=False)
        target_size = max(1, round(audio.size * target_rate / source_rate))
        source_positions = np.arange(audio.size, dtype=np.float64)
        target_positions = np.linspace(0, audio.size - 1, target_size)
        return np.interp(target_positions, source_positions, audio).astype(np.float32)

    @contextmanager
    def _open_capture(self) -> Iterator[tuple[int, str]]:
        device = self.settings.normalized_input_device()
        if self.settings.audio_backend == "sounddevice":
            info = sd.query_devices(device, "input")
            sample_rate = round(info["default_samplerate"])
            block_frames = sample_rate * self.settings.block_ms // 1000
            with sd.InputStream(
                device=device,
                channels=1,
                samplerate=sample_rate,
                blocksize=block_frames,
                dtype="float32",
                callback=self._callback,
            ):
                yield sample_rate, str(info["name"])
            return

        try:
            import pyaudiowpatch as pyaudio
        except ImportError as error:
            raise RuntimeError(
                "PyAudioWPatch is required for WASAPI loopback capture. "
                "Run: pip install -r requirements-nvidia.txt"
            ) from error

        with pyaudio.PyAudio() as audio:
            info = audio.get_device_info_by_index(int(device))
            sample_rate = round(info["defaultSampleRate"])
            channels = max(1, int(info["maxInputChannels"]))
            block_frames = sample_rate * self.settings.block_ms // 1000

            def loopback_callback(in_data, frame_count, time_info, status):
                samples = np.frombuffer(in_data, dtype=np.float32)
                if channels > 1:
                    samples = samples.reshape(-1, channels)
                self._queue_block(samples)
                return (None, pyaudio.paContinue)

            stream = audio.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=int(info["index"]),
                frames_per_buffer=block_frames,
                stream_callback=loopback_callback,
            )
            try:
                stream.start_stream()
                yield sample_rate, str(info["name"])
            finally:
                stream.stop_stream()
                stream.close()

    def run(self) -> None:
        silence_blocks = max(1, math.ceil(self.settings.silence_ms / self.settings.block_ms))
        min_blocks = max(1, math.ceil(self.settings.min_speech_ms / self.settings.block_ms))
        max_blocks = max(1, math.ceil(self.settings.max_phrase_ms / self.settings.block_ms))
        phrase: list[np.ndarray] = []
        pre_roll: deque[np.ndarray] = deque(maxlen=2)
        quiet = 0
        voiced_blocks = 0
        speaking = False

        with self._open_capture() as (input_sample_rate, device_name):
            print(f"Listening to '{device_name}' at {input_sample_rate} Hz...")
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
                        audio = np.concatenate(phrase)
                        self.on_phrase(
                            self._resample(
                                audio,
                                source_rate=input_sample_rate,
                                target_rate=self.settings.sample_rate,
                            )
                        )
                    phrase = []
                    quiet = 0
                    voiced_blocks = 0
                    speaking = False

    def stop(self) -> None:
        self._stop.set()
