from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from desktop import prepare_user_directory
from translator.highlights import load_highlight_config


class DesktopFilesTests(unittest.TestCase):
    def test_closing_desktop_stops_server_without_starting_microphone(self):
        import main

        webview = Mock()
        with patch.dict("sys.modules", {"webview": webview}), \
             patch("sys.argv", ["desktop.py"]), \
             patch("main.Settings.from_file", return_value=main.Settings()), \
             patch("main.load_highlight_config", return_value=([], {})), \
             patch("main.make_server") as make_server, \
             patch("main.PhraseRecorder") as recorder:
            main.main(desktop=True)
        webview.create_window.assert_called_once()
        webview.start.assert_called_once_with(gui="edgechromium")
        recorder.assert_not_called()
        make_server.return_value.shutdown.assert_called_once()
        make_server.return_value.server_close.assert_called_once()

    def test_first_run_creates_files_and_updates_preserve_personal_settings(self):
        resources = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "user"
            prepare_user_directory(resources, destination)
            self.assertTrue((destination / "config.json").is_file())
            self.assertTrue((destination / "config.gaming.json").is_file())
            terms = destination / "highlight_terms.txt"
            self.assertEqual(terms.read_text(), "")
            terms.write_text("My channel\n", encoding="utf-8")
            (destination / "config.json").write_text('{"model": "small"}', encoding="utf-8")
            prepare_user_directory(resources, destination)
            self.assertEqual(terms.read_text(), "My channel\n")
            self.assertEqual((destination / "config.json").read_text(), '{"model": "small"}')

    def test_source_mode_creates_missing_terms_without_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "highlight_terms.txt"
            self.assertEqual(load_highlight_config(str(path)), ([], {}))
            self.assertEqual(path.read_text(), "")


if __name__ == "__main__":
    unittest.main()
