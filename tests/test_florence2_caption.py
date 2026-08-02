import unittest

import numpy as np

from image2prompt.florence2_caption import _updated_past


class Florence2CaptionTests(unittest.TestCase):
    def test_keeps_encoder_cache_after_the_first_token(self) -> None:
        encoder = np.ones((1, 12, 10, 64), dtype=np.float32)
        decoder = np.ones((1, 12, 1, 64), dtype=np.float32)
        previous = {
            "past_key_values.0.encoder.key": encoder,
            "past_key_values.0.decoder.key": decoder,
        }

        updated = _updated_past(
            previous,
            ["present.0.encoder.key", "present.0.decoder.key"],
            [
                np.empty((0, 12, 1, 64), dtype=np.float32),
                np.ones((1, 12, 2, 64), dtype=np.float32),
            ],
        )

        self.assertIs(updated["past_key_values.0.encoder.key"], encoder)
        self.assertEqual(updated["past_key_values.0.decoder.key"].shape[2], 2)


if __name__ == "__main__":
    unittest.main()
