import unittest

import numpy as np

from image2prompt.wd_tagger import _select_tags


class TagSelectionTests(unittest.TestCase):
    def test_selects_rating_and_thresholded_tags_in_score_order(self) -> None:
        result = _select_tags(
            ["general", "explicit", "blue_eyes", "solo", "hatsune_miku"],
            [9, 9, 0, 0, 4],
            np.array([0.1, 0.9, 0.6, 0.8, 0.9], dtype=np.float32),
            0.35,
            0.85,
        )

        self.assertEqual(result["rating"]["tag"], "explicit")
        self.assertEqual(
            [tag["tag"] for tag in result["general"]],
            ["solo", "blue_eyes"],
        )
        self.assertEqual(
            result["prompt"],
            "hatsune_miku, solo, blue_eyes",
        )


if __name__ == "__main__":
    unittest.main()
