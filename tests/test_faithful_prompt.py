import unittest

from image2prompt.faithful_prompt import build_faithful_prompt


def tags(*names: str, score: float = 0.9) -> list[dict[str, object]]:
    return [{"tag": name, "score": score} for name in names]


class FaithfulPromptTests(unittest.TestCase):
    def test_removes_conflicts_in_sensitive_photo(self) -> None:
        result = build_faithful_prompt(
            tags(
                "1girl",
                "solo",
                "short_hair",
                "brown_hair",
                "topless",
                "panties",
                "bikini",
                "swimsuit",
                "covering_breasts",
                "photorealistic",
                "realistic",
            ),
            [],
        )
        prompt = result["prompt"]

        self.assertNotIn("[Image interpretation]", prompt)
        self.assertNotIn("[Environment settings]", prompt)
        self.assertIn("short brown hair", prompt)
        self.assertIn("topless and wearing panties", prompt)
        self.assertIn("covering her chest", prompt)
        self.assertIn("The visual style is photorealistic.", prompt)
        self.assertNotIn("bikini", prompt)
        self.assertNotIn("swimsuit", prompt)
        self.assertNotIn("The visual style is realistic.", prompt)

    def test_combines_supported_objects_and_actions(self) -> None:
        result = build_faithful_prompt(
            tags(
                "1girl",
                "solo",
                "black_hair",
                "medium_hair",
                "round_eyewear",
                "glasses",
                "holding_bottle",
                "drinking",
                "bottle",
                "car",
                "motor_vehicle",
                "convenience_store",
                "brand_name_imitation",
            ),
            [],
        )
        prompt = result["prompt"]

        self.assertIn("medium-length black hair", prompt)
        self.assertIn("round glasses", prompt)
        self.assertIn("holding and drinking from a bottle", prompt)
        self.assertIn("cars and a convenience store", prompt)
        self.assertNotIn("brand name", prompt)
        self.assertNotIn("vehicles", prompt)

    def test_uses_fixed_fidelity_threshold(self) -> None:
        result = build_faithful_prompt(
            [
                {"tag": "1girl", "score": 0.50},
                {"tag": "pink_hair", "score": 0.49},
            ],
            [],
        )

        self.assertIn("one female subject", result["prompt"])
        self.assertNotIn("pink hair", result["prompt"])

    def test_adds_detected_composition_and_lighting(self) -> None:
        result = build_faithful_prompt(
            tags(
                "1girl",
                "full_body",
                "from_below",
                "depth_of_field",
                "backlighting",
                "light_rays",
            ),
            [],
        )
        prompt = result["prompt"]

        self.assertIn(
            "The framing uses a full-body view.",
            prompt,
        )
        self.assertIn(
            "The camera uses a low-angle viewpoint.",
            prompt,
        )
        self.assertIn(
            "The focus uses depth of field.",
            prompt,
        )
        self.assertIn(
            "The lighting uses backlighting and visible light rays.",
            prompt,
        )
        self.assertNotIn("full body", prompt)
        self.assertEqual(
            result["image_interpretation"],
            "The image shows one female subject.",
        )
        self.assertIn("The camera uses", result["environment_settings"])

    def test_adds_only_the_selected_environment_preset(self) -> None:
        default_result = build_faithful_prompt(
            tags("1girl", "photorealistic"),
            [],
        )
        anime_result = build_faithful_prompt(
            tags("1girl", "photorealistic"),
            [],
            environment_preset="anime_clean",
        )

        self.assertIn("photorealistic", default_result["prompt"])
        self.assertNotIn("precise line art", default_result["prompt"])
        self.assertIn("precise line art", anime_result["environment_settings"])
        self.assertNotIn("photorealistic", anime_result["prompt"])
        self.assertEqual(anime_result["environment_preset"], "anime_clean")

        with self.assertRaises(ValueError):
            build_faithful_prompt(
                tags("1girl"),
                [],
                environment_preset="unknown",
            )


if __name__ == "__main__":
    unittest.main()
