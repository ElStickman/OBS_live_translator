from __future__ import annotations

import queue
import threading

import numpy as np
from faster_whisper import WhisperModel

from .config import Settings
from .state import CaptionStore


class TranslationWorker:
    def __init__(
        self,
        settings: Settings,
        captions: CaptionStore,
        highlight_terms: list[str] | None = None,
    ) -> None:
        self.settings = settings
        self.captions = captions
        self.highlight_terms = highlight_terms or []
        self._phrases: queue.Queue[np.ndarray] = queue.Queue(maxsize=3)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._model: WhisperModel | None = None

    def start(self) -> None:
        print(
            f"Loading Whisper model '{self.settings.model}' "
            f"on {self.settings.device} ({self.settings.compute_type})..."
        )
        try:
            self._model = WhisperModel(
                self.settings.model,
                device=self.settings.device,
                compute_type=self.settings.compute_type,
            )
            self._warm_up()
        except RuntimeError as error:
            if self.settings.device == "cuda":
                raise RuntimeError(
                    "Whisper could not start on the NVIDIA GPU. Confirm that the "
                    "NVIDIA driver, CUDA 12 cuBLAS and CUDA 12 cuDNN 9 are installed "
                    "and available in PATH."
                ) from error
            raise
        print("Whisper model ready.")
        self._thread.start()

    def _transcribe(self, audio: np.ndarray):
        if self._model is None:
            raise RuntimeError("Translation worker started without a Whisper model")
        return self._model.transcribe(
            audio,
            language="es",
            task="translate",
            beam_size=1,
            # Audio is already segmented by PhraseRecorder. A second VAD pass
            # tends to discard short phrases such as "mira" or "mira esto".
            vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt=(
                "Names and special terms: " + ", ".join(self.highlight_terms)
                if self.highlight_terms
                else None
            ),
        )

    def _warm_up(self) -> None:
        segments, _ = self._transcribe(
            np.zeros(self.settings.sample_rate, dtype=np.float32)
        )
        list(segments)

    def submit(self, audio: np.ndarray) -> None:
        try:
            self._phrases.put_nowait(audio)
        except queue.Full:
            print("Translator is behind; dropping one phrase.")

    def _run(self) -> None:
        if self._model is None:
            raise RuntimeError("Translation worker started without a Whisper model")
        while True:
            audio = self._phrases.get()
            try:
                segments, info = self._transcribe(audio)
                text = " ".join(segment.text.strip() for segment in segments).strip()
                if text:
                    print(f"EN: {text}")
                    self.captions.publish(text, info.language, self.settings.caption_seconds)
            except Exception as error:
                print(f"Translation failed: {error}")
            finally:
                self._phrases.task_done()
