import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gradio as gr

from image2prompt.ui import load_folder, run_analysis, select_folder_image


class UiTests(unittest.TestCase):
    def test_loads_and_selects_one_folder_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "a.jpg"
            second = Path(directory) / "b.png"
            first.write_bytes(b"first")
            second.write_bytes(b"second")

            gallery, paths, status = load_folder([str(second), str(first)])
            selected, selected_status = select_folder_image(
                paths,
                gr.SelectData(None, {"index": 1, "value": None}),
            )

        self.assertEqual(gallery, [(str(first), "a.jpg"), (str(second), "b.png")])
        self.assertEqual(selected, str(second))
        self.assertIn("2枚", status)
        self.assertIn("b.png", selected_status)

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
