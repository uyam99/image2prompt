import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from image2prompt.natural_prompt import (
    _data_dir,
    _local_model_dir,
    _uv_path,
    compose_prompt,
    split_florence_prompt,
)


class NaturalPromptTests(unittest.TestCase):
    def test_separates_style_and_removes_speculative_details(self) -> None:
        content, style = split_florence_prompt(
            "A young woman looks out of a window",
            "Photo of a 20-year-old Asian woman by a window. "
            "The lighting is soft and natural. "
            "The overall mood is peaceful. The image has a watermark.",
        )

        self.assertEqual(style, "photorealistic photograph")
        self.assertIn("young adult woman", content)
        self.assertIn("lighting is soft and natural", content)
        self.assertNotIn("20-year-old", content)
        self.assertNotIn("Asian", content)
        self.assertNotIn("mood", content)
        self.assertNotIn("watermark", content)

    def test_joins_only_non_empty_user_layers(self) -> None:
        self.assertEqual(
            compose_prompt("Florence content", "photo", "", "camera"),
            "Florence content\n\nphoto\n\ncamera",
        )

    def test_uses_external_data_and_optional_local_model_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            (model / "model.safetensors").touch()
            with patch.dict(
                "image2prompt.natural_prompt.os.environ",
                {
                    "IMAGE2PROMPT_DATA_DIR": directory,
                    "IMAGE2PROMPT_FLORENCE_MODEL_DIR": str(model),
                },
            ):
                self.assertEqual(_data_dir(), Path(directory))
                self.assertEqual(_local_model_dir(), model)

    def test_finds_bundled_windows_uv_executable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundled = root / "bin/uv.exe"
            bundled.parent.mkdir()
            bundled.touch()
            with (
                patch("image2prompt.natural_prompt.sys.platform", "win32"),
                patch("image2prompt.natural_prompt._resource_root", return_value=root),
                patch.dict("image2prompt.natural_prompt.os.environ", {}, clear=True),
            ):
                self.assertEqual(_uv_path(), bundled)


if __name__ == "__main__":
    unittest.main()
