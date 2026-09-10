import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from translator.devices import AudioSource
from translator.state import CaptionStore
from translator.web import create_app


class AudioSelectionTests(unittest.TestCase):
    @patch("translator.web.list_audio_sources", return_value=[AudioSource("sounddevice", 7, "Microphone", 1, 48000)])
    def test_audio_selection_survives_app_restart(self, _sources):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "selection.json")
            client = create_app(CaptionStore(), selection_path=path).test_client()
            self.assertIsNone(client.get("/api/audio-selection").get_json()["device"])
            self.assertEqual(client.post("/api/audio-selection", json={"backend": "sounddevice", "device": 7}).status_code, 200)
            restarted = create_app(CaptionStore(), selection_path=path).test_client()
            self.assertEqual(restarted.get("/api/audio-selection").get_json(), {"backend": "sounddevice", "device": 7})

    def test_invalid_request_shapes_return_client_errors(self):
        client = create_app(CaptionStore()).test_client()
        for method, endpoint in [("post", "/api/audio-selection"),
                                 ("put", "/api/language-mode"),
                                 ("put", "/api/highlight-terms")]:
            for payload in [[], [1], "text", 42, True]:
                with self.subTest(endpoint=endpoint, payload=payload):
                    response = getattr(client, method)(endpoint, json=payload)
                    self.assertEqual(response.status_code, 400)
        for payload in [{"backend": [], "device": 1},
                        {"backend": "sounddevice", "device": True},
                        {"backend": "sounddevice", "device": 1.5}]:
            self.assertEqual(client.post("/api/audio-selection", json=payload).status_code, 400)
        self.assertEqual(client.put("/api/language-mode", json={"mode": []}).status_code, 400)

    @patch("translator.web.Path.exists", return_value=True)
    @patch("translator.web.Path.read_text", return_value="broken JSON")
    @patch("translator.web.Path.write_text")
    def test_does_not_overwrite_corrupt_saved_settings(self, write, _read, _exists):
        options = {"mode": "english_spanish"}
        client = create_app(CaptionStore(), language_options=options).test_client()
        response = client.put("/api/language-mode", json={"mode": "all"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())
        self.assertEqual(options["mode"], "english_spanish")
        write.assert_not_called()

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
