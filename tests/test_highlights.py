import unittest
from unittest.mock import patch

from translator.highlights import load_highlight_config, load_highlight_terms


class HighlightTermsTests(unittest.TestCase):
    @patch("translator.highlights.Path.exists", return_value=True)
    @patch(
        "translator.highlights.Path.read_text",
        return_value="# comment\nExampleBrand\nexamplebrand\nSpecial phrase\n\n",
    )
    def test_loads_terms_ignoring_comments_blanks_and_case_duplicates(
        self, _mock_read, _mock_exists
    ):
        self.assertEqual(
            load_highlight_terms("terms.txt"),
            ["ExampleBrand", "Special phrase"],
        )

    @patch("translator.highlights.Path.exists", return_value=True)
    @patch(
        "translator.highlights.Path.read_text",
        return_value="Default term\nCustom term\t#12ABef\nInvalid\tnot-a-color\n",
    )
    def test_loads_custom_colors_and_defaults_invalid_colors_to_yellow(
        self, _mock_read, _mock_exists
    ):
        terms, colors = load_highlight_config("terms.txt")

        self.assertEqual(terms, ["Default term", "Custom term", "Invalid"])
        self.assertEqual(colors["default term"], "#ffd400")
        self.assertEqual(colors["custom term"], "#12abef")
        self.assertEqual(colors["invalid"], "#ffd400")


if __name__ == "__main__":
    unittest.main()
