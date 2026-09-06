import unittest
from unittest.mock import patch

from translator.config import Settings


class SettingsTests(unittest.TestCase):
    @patch(
        "translator.config.Path.read_text",
        return_value='{"model": "small", "input_device": 2}',
    )
    def test_loads_json_and_keeps_defaults(self, _mock_read):
        settings = Settings.from_file("config.json")

        self.assertEqual(settings.model, "small")
        self.assertEqual(settings.input_device, 2)
        self.assertEqual(settings.device, "cuda")

    @patch("translator.config.Path.read_text", return_value='{"unknown": true}')
    def test_rejects_unknown_keys(self, _mock_read):
        with self.assertRaisesRegex(ValueError, "Unknown configuration keys"):
            Settings.from_file("config.json")

    def test_rejects_zero_block_duration(self):
        with self.assertRaisesRegex(ValueError, "block_ms"):
            Settings(block_ms=0)

    def test_rejects_invalid_port(self):
        with self.assertRaisesRegex(ValueError, "port"):
            Settings(port=70000)

    def test_rejects_unknown_audio_backend(self):
        with self.assertRaisesRegex(ValueError, "audio_backend"):
            Settings(audio_backend="unknown")

    def test_rejects_unknown_language_mode(self):
        with self.assertRaisesRegex(ValueError, "language_mode"):
            Settings(language_mode="unknown")

    def test_rejects_zero_max_pending_phrases(self):
        with self.assertRaisesRegex(ValueError, "max_pending_phrases"):
            Settings(max_pending_phrases=0)

    def test_rejects_zero_language_detection_interval(self):
        with self.assertRaisesRegex(ValueError, "language_detection_interval"):
            Settings(language_detection_interval=0)

    def test_rejects_invalid_no_speech_threshold(self):
        with self.assertRaisesRegex(ValueError, "no_speech_threshold"):
            Settings(no_speech_threshold=1.1)


if __name__ == "__main__":
    unittest.main()
