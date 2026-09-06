import json
import unittest
from unittest.mock import Mock, patch

from translator.devices import AudioSource
from translator.state import CaptionStore
from translator.web import create_app


class AudioSelectionTests(unittest.TestCase):
    def test_settings_links_to_subtitle_preview(self):
        response = create_app(CaptionStore()).test_client().get("/settings")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/"', response.data)
        self.assertIn(b"Open subtitle preview", response.data)
        response.close()

    @patch("translator.web.Path.write_text")
    @patch("translator.web.Path.read_text", return_value='{"input_device": null}')
    @patch(
        "translator.web.list_audio_sources",
        return_value=[AudioSource("wasapi_loopback", 33, "Sonar Chat", 2, 48000)],
    )
    def test_saves_selected_audio_source(
        self, _mock_sources, _mock_read, mock_write
    ):
        selected = Mock()
        client = create_app(
            CaptionStore(), selection_path="audio_selection.json", on_audio_selected=selected
        ).test_client()

        response = client.post(
            "/api/audio-selection",
            json={"backend": "wasapi_loopback", "device": 33},
        )
        second_response = client.post(
            "/api/audio-selection",
            json={"backend": "wasapi_loopback", "device": 33},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        saved = json.loads(mock_write.call_args.args[0])
        self.assertEqual(saved["audio_backend"], "wasapi_loopback")
        self.assertEqual(saved["input_device"], 33)
        self.assertEqual(selected.call_count, 2)


class HighlightTermsTests(unittest.TestCase):
    @patch("translator.web.Path.write_text")
    def test_updates_highlight_terms_without_restart(self, mock_write):
        active_terms = ["Old name"]
        active_colors = {"old name": "#ffd400"}
        client = create_app(
            CaptionStore(),
            highlight_terms=active_terms,
            highlight_colors=active_colors,
            highlight_terms_path="highlight_terms.txt",
        ).test_client()

        response = client.put(
            "/api/highlight-terms",
            json={
                "terms": [
                    {"term": " ElStickman ", "color": "#ff3366"},
                    {"term": "elstickman", "color": "#000000"},
                    {"term": "Mati", "color": "#ffd400"},
                    {"term": "", "color": "#ffd400"},
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(active_terms, ["ElStickman", "Mati"])
        self.assertEqual(active_colors, {"elstickman": "#ff3366", "mati": "#ffd400"})
        self.assertEqual(mock_write.call_args.args[0], "ElStickman\t#ff3366\nMati\n")
        self.assertEqual(client.get("/api/caption").get_json()["highlight_terms"], active_terms)
        self.assertEqual(
            client.get("/api/caption").get_json()["highlights"][0],
            {"term": "ElStickman", "color": "#ff3366"},
        )

        empty_response = client.put("/api/highlight-terms", json={"terms": []})
        self.assertEqual(empty_response.status_code, 200)
        self.assertEqual(active_terms, [])
        self.assertEqual(active_colors, {})
        self.assertEqual(mock_write.call_args.args[0], "")

    def test_rejects_invalid_highlight_color(self):
        client = create_app(CaptionStore()).test_client()

        response = client.put(
            "/api/highlight-terms",
            json={"terms": [{"term": "Example", "color": "yellow"}]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid color", response.get_json()["error"])


class LanguageModeTests(unittest.TestCase):
    @patch("translator.web.Path.exists", return_value=False)
    @patch("translator.web.Path.write_text")
    def test_updates_language_mode_without_restart(self, mock_write, _mock_exists):
        options = {"mode": "english_spanish"}
        client = create_app(CaptionStore(), language_options=options).test_client()

        response = client.put("/api/language-mode", json={"mode": "all"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(options["mode"], "all")
        self.assertEqual(json.loads(mock_write.call_args.args[0])["language_mode"], "all")


if __name__ == "__main__":
    unittest.main()
