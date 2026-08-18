import unittest
from unittest.mock import patch

from translator.highlights import load_highlight_terms


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


if __name__ == "__main__":
    unittest.main()
