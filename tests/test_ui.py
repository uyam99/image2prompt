import unittest
from unittest.mock import patch

import gradio as gr

from image2prompt.ui import run_analysis


class UiTests(unittest.TestCase):
    @patch(
        "image2prompt.ui.analyze",
        return_value={
            "total_seconds": 1.25,
            "danbooru": {
                "prompt": "1girl, solo",
                "rating": {"tag": "general", "score": 0.9},
            },
            "natural_language": {"prompt": "A girl standing alone."},
        },
    )
    def test_formats_analysis_for_display(self, analyze_mock) -> None:
        tags, natural, status = run_analysis("image.jpg", 0.35, 0.85, 128.0)

        self.assertEqual(tags, "1girl, solo")
        self.assertEqual(natural, "A girl standing alone.")
        self.assertIn("1.25秒", status)
        self.assertIn("general", status)
        self.assertEqual(analyze_mock.call_args.kwargs["max_new_tokens"], 128)

    def test_requires_an_image(self) -> None:
        with self.assertRaises(gr.Error):
            run_analysis(None, 0.35, 0.85, 128)


if __name__ == "__main__":
    unittest.main()
