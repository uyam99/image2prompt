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
        return_value={
            "input": "image.jpg",
            "prompt": "tag prompt",
            "general": [
                {"tag": "1girl", "score": 0.99},
                {"tag": "solo", "score": 0.90},
            ],
            "character": [],
        },
    )
    def test_combines_prompt_formats(self, _predict, _caption) -> None:
        result = analyze(Path("image.jpg"))

        self.assertEqual(result["danbooru"]["prompt"], "tag prompt")
        self.assertEqual(
            result["faithful_prompt"]["prompt"],
            "The image shows one female subject alone.",
        )
        self.assertEqual(
            result["natural_language"]["prompt"],
            "natural prompt",
        )
        self.assertNotIn("input", result["danbooru"])
        self.assertNotIn("input", result["natural_language"])

    @patch("image2prompt.analyze.caption")
    @patch(
        "image2prompt.analyze.predict",
        return_value={
            "input": "image.jpg",
            "prompt": "tag prompt",
            "general": [{"tag": "1girl", "score": 0.99}],
            "character": [],
        },
    )
    def test_can_skip_reference_caption(self, _predict, caption_mock) -> None:
        result = analyze(Path("image.jpg"), include_natural_language=False)

        caption_mock.assert_not_called()
        self.assertNotIn("natural_language", result)


if __name__ == "__main__":
    unittest.main()
