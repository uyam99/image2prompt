import unittest
from pathlib import Path
from unittest.mock import patch

from image2prompt.analyze import analyze


class AnalyzeTests(unittest.TestCase):
    @patch(
        "image2prompt.analyze.caption",
        return_value={"input": "image.jpg", "prompt": "natural prompt"},
    )
    @patch(
        "image2prompt.analyze.predict",
        return_value={"input": "image.jpg", "prompt": "tag prompt"},
    )
    def test_combines_both_prompt_formats(self, _predict, _caption) -> None:
        result = analyze(Path("image.jpg"))

        self.assertEqual(result["danbooru"]["prompt"], "tag prompt")
        self.assertEqual(
            result["natural_language"]["prompt"],
            "natural prompt",
        )
        self.assertNotIn("input", result["danbooru"])
        self.assertNotIn("input", result["natural_language"])


if __name__ == "__main__":
    unittest.main()
