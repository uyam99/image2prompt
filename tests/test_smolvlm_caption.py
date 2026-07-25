import unittest

import numpy as np

from image2prompt.smolvlm_caption import _extend_attention_mask


class CaptionGenerationTests(unittest.TestCase):
    def test_attention_mask_keeps_past_tokens(self) -> None:
        mask = np.ones((1, 3), dtype=np.int64)
        next_token = np.array([[42]], dtype=np.int64)

        extended = _extend_attention_mask(mask, next_token)

        np.testing.assert_array_equal(
            extended,
            np.ones((1, 4), dtype=np.int64),
        )


if __name__ == "__main__":
    unittest.main()
