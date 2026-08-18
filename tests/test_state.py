import unittest
from unittest.mock import patch

from translator.state import CaptionStore


class CaptionStoreTests(unittest.TestCase):
    @patch("translator.state.time.time", return_value=100.0)
    def test_publish_returns_visible_caption(self, _mock_time):
        store = CaptionStore()
        store.publish("Hello", "es", 8)

        self.assertEqual(store.snapshot()["text"], "Hello")
        self.assertTrue(store.snapshot()["visible"])

    def test_empty_store_is_hidden(self):
        self.assertFalse(CaptionStore().snapshot()["visible"])

    @patch("translator.state.time.time", side_effect=[100.0, 109.0])
    def test_caption_expires(self, _mock_time):
        store = CaptionStore()
        store.publish("Hello", "es", 8)

        self.assertFalse(store.snapshot()["visible"])


if __name__ == "__main__":
    unittest.main()
