import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gradio as gr
from PIL import Image

from image2prompt.ui import (
    DEFAULT_SETTINGS,
    _default_settings_path,
    _sort_folder_images,
    choose_folder,
    estimate_prompt_tokens,
    load_folder,
    load_settings,
    refresh_folder,
    run_analysis,
    save_settings,
    select_folder_image,
)


class UiTests(unittest.TestCase):
    @patch("image2prompt.ui.sys.platform", "win32")
    @patch.dict(
        "image2prompt.ui.os.environ",
        {"APPDATA": r"C:\Users\test\AppData\Roaming"},
    )
    def test_uses_windows_settings_folder(self) -> None:
        self.assertEqual(
            _default_settings_path(),
            Path(r"C:\Users\test\AppData\Roaming")
            / "image2prompt"
            / "settings.json",
        )

    def test_persists_settings_and_recovers_from_invalid_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            save_settings(0.42, 0.91, "anime_clean", path)

            self.assertEqual(
                load_settings(path),
                {
                    "general_threshold": 0.42,
                    "character_threshold": 0.91,
                    "environment_preset": "anime_clean",
                },
            )

            path.write_text(
                '{"general_threshold": 0.4, "character_threshold": 0.8}',
                encoding="utf-8",
            )
            self.assertEqual(load_settings(path)["environment_preset"], "none")

            path.write_text("{invalid", encoding="utf-8")
            self.assertEqual(load_settings(path), DEFAULT_SETTINGS)

    @patch("image2prompt.ui.sys.platform", "linux")
    def test_sorts_reloads_and_selects_folder_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "image2.jpg"
            second = Path(directory) / "image10.jpg"
            third = Path(directory) / "sample.png"
            ignored = Path(directory) / ".DS_Store"
            Image.new("RGB", (12, 8), "red").save(first)
            Image.new("RGB", (8, 12), "green").save(second)
            Image.new("RGB", (10, 10), "blue").save(third)
            ignored.write_bytes(b"metadata")
            os.utime(first, (100, 100))
            os.utime(second, (300, 300))
            os.utime(third, (200, 200))

            gallery, paths, status = load_folder(
                directory,
                "name",
                "ascending",
            )
            preview, selected, selected_status = select_folder_image(
                paths,
                gr.SelectData(None, {"index": 1, "value": None}),
            )
            _, by_date, _, retained_preview, retained = refresh_folder(
                directory,
                "modified",
                "descending",
                selected,
                preview,
            )
            added = Path(directory) / "added.gif"
            Image.new("RGB", (9, 9), "yellow").save(added)
            _, reloaded, _, _, _ = refresh_folder(
                directory,
                "kind",
                "ascending",
                selected,
                preview,
            )
            second.unlink()
            _, _, _, removed_preview, removed = refresh_folder(
                directory,
                "name",
                "ascending",
                selected,
                preview,
            )

        self.assertEqual(paths, [str(first), str(second), str(third)])
        self.assertTrue(all(Path(path).is_file() for path in gallery))
        self.assertNotEqual(gallery, paths)
        self.assertEqual(selected, str(second))
        self.assertEqual(by_date, [str(second), str(third), str(first)])
        self.assertEqual(retained, str(second))
        self.assertEqual(retained_preview, preview)
        self.assertEqual(
            reloaded,
            [str(added), str(first), str(second), str(third)],
        )
        self.assertIsNone(removed)
        self.assertIsNone(removed_preview)
        self.assertIn("3枚", status)
        self.assertIn("名前・昇順", status)
        self.assertIn("image10.jpg", selected_status)

    @patch("image2prompt.ui.sys.platform", "darwin")
    @patch("image2prompt.ui.subprocess.run")
    def test_uses_finder_name_order_on_macos(self, run_mock) -> None:
        names = [
            "HN7.jpeg",
            "HN_7.jpeg",
            "HN10.jpeg",
            "HN2.jpeg",
            "HNA.jpeg",
        ]
        finder_order = [
            "HN_7.jpeg",
            "HN2.jpeg",
            "HN7.jpeg",
            "HN10.jpeg",
            "HNA.jpeg",
        ]
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = json.dumps(finder_order)

        paths = [Path(name) for name in names]
        result = _sort_folder_images(paths, "name", "ascending")

        self.assertEqual([path.name for path in result], finder_order)
        self.assertEqual(
            json.loads(run_mock.call_args.kwargs["input"]),
            names,
        )

    @patch("image2prompt.ui.sys.platform", "darwin")
    @patch("image2prompt.ui.subprocess.run")
    def test_chooses_a_real_folder_with_finder(self, run_mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "a.jpg"
            Image.new("RGB", (10, 10), "red").save(image)
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = f"{directory}\n"
            run_mock.return_value.stderr = ""

            folder, gallery, paths, status, preview, selected = choose_folder(
                "name",
                "ascending",
            )

        self.assertEqual(folder, directory)
        self.assertEqual(len(gallery), 1)
        self.assertNotEqual(gallery, paths)
        self.assertEqual(paths, [str(image)])
        self.assertIn(directory, status)
        self.assertIsNone(preview)
        self.assertIsNone(selected)
        run_mock.assert_called_once()

    @patch("image2prompt.ui.sys.platform", "win32")
    def test_chooses_a_real_folder_with_windows_dialog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "a.jpg"
            Image.new("RGB", (10, 10), "red").save(image)
            window = SimpleNamespace(
                create_file_dialog=lambda _dialog_type: (directory,)
            )
            webview = SimpleNamespace(
                active_window=lambda: window,
                FileDialog=SimpleNamespace(FOLDER="folder"),
            )
            with patch.dict("sys.modules", {"webview": webview}):
                folder, _, paths, _, _, _ = choose_folder("name", "ascending")

        self.assertEqual(folder, directory)
        self.assertEqual(paths, [str(image)])

    @patch(
        "image2prompt.ui.analyze",
        return_value={
            "total_seconds": 1.25,
            "danbooru": {
                "prompt": "1girl, solo",
                "rating": {"tag": "general", "score": 0.9},
            },
            "faithful_prompt": {
                "prompt": "The image shows one female subject alone."
            },
        },
    )
    def test_formats_analysis_for_display(self, analyze_mock) -> None:
        faithful, faithful_tokens, tags, tag_tokens, status = run_analysis(
            "preview.jpg",
            "source.jpg",
            0.35,
            0.85,
            "anime_clean",
        )

        self.assertEqual(faithful, "The image shows one female subject alone.")
        self.assertEqual(tags, "1girl, solo")
        self.assertIn("11", faithful_tokens)
        self.assertIn("512", faithful_tokens)
        self.assertIn("3", tag_tokens)
        self.assertIn("1.25秒", status)
        self.assertIn("general", status)
        self.assertFalse(
            analyze_mock.call_args.kwargs["include_natural_language"]
        )
        self.assertEqual(
            analyze_mock.call_args.kwargs["environment_preset"],
            "anime_clean",
        )
        self.assertEqual(analyze_mock.call_args.args[0], Path("source.jpg"))

    def test_requires_an_image(self) -> None:
        with self.assertRaises(gr.Error):
            run_analysis(None, None, 0.35, 0.85, "none")

    def test_estimates_tokens_without_enforcing_the_reference(self) -> None:
        self.assertEqual(estimate_prompt_tokens(""), 0)
        self.assertEqual(estimate_prompt_tokens("abcd"), 1)
        self.assertEqual(estimate_prompt_tokens("abcde"), 2)
        self.assertEqual(estimate_prompt_tokens("x" * 2049), 513)


if __name__ == "__main__":
    unittest.main()
