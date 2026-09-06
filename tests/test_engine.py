import unittest
from unittest.mock import Mock

import numpy as np

from translator.config import Settings
from translator.engine import TranslationWorker
from translator.state import CaptionStore


class LanguageRestrictionTests(unittest.TestCase):
    def test_keeps_reference_to_initially_empty_dynamic_highlight_list(self):
        terms = []
        worker = TranslationWorker(Settings(), CaptionStore(), highlight_terms=terms)

        terms.append("ElStickman")

        self.assertEqual(worker.highlight_terms, ["ElStickman"])

    def test_selects_best_probability_only_from_english_and_spanish(self):
        worker = TranslationWorker(
            Settings(), CaptionStore(), language_options={"mode": "english_spanish"}
        )
        worker._model = Mock()
        worker._model.detect_language.return_value = (
            "fr", 0.8, [("fr", 0.8), ("es", 0.15), ("en", 0.05)]
        )

        worker._transcribe(np.zeros(16000, dtype=np.float32))

        self.assertEqual(worker._model.transcribe.call_args.kwargs["language"], "es")

    def test_all_languages_uses_automatic_detection(self):
        worker = TranslationWorker(
            Settings(), CaptionStore(), language_options={"mode": "all"}
        )
        worker._model = Mock()

        worker._transcribe(np.zeros(16000, dtype=np.float32))

        worker._model.detect_language.assert_not_called()
        self.assertIsNone(worker._model.transcribe.call_args.kwargs["language"])

    def test_passes_no_speech_threshold_to_whisper(self):
        worker = TranslationWorker(
            Settings(no_speech_threshold=0.55),
            CaptionStore(),
            language_options={"mode": "all"},
        )
        worker._model = Mock()

        worker._transcribe(np.zeros(16000, dtype=np.float32))

        self.assertEqual(
            worker._model.transcribe.call_args.kwargs["no_speech_threshold"], 0.55
        )

    def test_reuses_detected_language_at_configured_interval(self):
        worker = TranslationWorker(
            Settings(language_detection_interval=3),
            CaptionStore(),
            language_options={"mode": "english_spanish"},
        )
        worker._model = Mock()
        worker._model.detect_language.return_value = (
            "es", 0.9, [("es", 0.9), ("en", 0.1)]
        )
        audio = np.zeros(16000, dtype=np.float32)

        for _ in range(4):
            worker._transcribe(audio)

        self.assertEqual(worker._model.detect_language.call_count, 2)

    def test_replaces_pending_phrase_when_configured_queue_is_full(self):
        worker = TranslationWorker(
            Settings(max_pending_phrases=1), CaptionStore()
        )
        first_audio = np.zeros(16000, dtype=np.float32)
        latest_audio = np.ones(16000, dtype=np.float32)

        worker.submit(first_audio)
        worker.submit(latest_audio)

        self.assertEqual(worker._phrases.qsize(), 1)
        np.testing.assert_array_equal(worker._phrases.get_nowait(), latest_audio)


if __name__ == "__main__":
    unittest.main()
