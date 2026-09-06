import unittest

import numpy as np

from translator.audio import PhraseRecorder


class ResampleTests(unittest.TestCase):
    def test_resamples_48khz_audio_to_16khz(self):
        audio = np.linspace(-1, 1, 48000, dtype=np.float32)

        result = PhraseRecorder._resample(audio, 48000, 16000)

        self.assertEqual(result.shape, (16000,))
        self.assertEqual(result.dtype, np.float32)

    def test_same_rate_returns_float32(self):
        audio = np.ones(100, dtype=np.float64)

        result = PhraseRecorder._resample(audio, 16000, 16000)

        self.assertEqual(result.dtype, np.float32)


if __name__ == "__main__":
    unittest.main()
