"""Build a conservative natural-language prompt from WD tags."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .image_processing import ImageInputError
from .wd_tagger import DEFAULT_MODEL_DIR, predict

DEFAULT_THRESHOLD = 0.50

EXCLUDED_TAGS = {
    "brand_name_imitation",
    "breasts",
    "feet",
    "jewelry",
    "legs",
    "signature",
    "text",
    "toenails",
    "toes",
    "watermark",
}

APPEARANCE_TAGS = {
    "black_eyes": "black eyes",
    "blunt_bangs": "blunt bangs",
    "brown_eyes": "brown eyes",
    "double_bun": "a double bun",
    "hair_bun": "a hair bun",
    "large_breasts": "large breasts",
    "medium_breasts": "medium breasts",
    "messy_hair": "messy hair",
    "sidelocks": "sidelocks",
    "small_breasts": "small breasts",
    "yellow_eyes": "yellow eyes",
}

CLOTHING_TAGS = {
    "bare_shoulders": "bare shoulders",
    "black_choker": "a black choker",
    "brown_shorts": "brown shorts",
    "cardigan": "a cardigan",
    "choker": "a choker",
    "dress": "a dress",
    "glasses": "glasses",
    "long_sleeves": "long sleeves",
    "necklace": "a necklace",
    "off_shoulder": "off-shoulder clothing",
    "panties": "panties",
    "round_eyewear": "round glasses",
    "sandals": "sandals",
    "shorts": "shorts",
    "tank_top": "a tank top",
    "underwear": "underwear",
    "white_dress": "a white dress",
    "white_footwear": "white footwear",
}

ACTION_TAGS = {
    "covering_breasts": "covering her chest",
    "covering_privates": "covering her lower body",
    "knees_together_feet_apart": "keeping her knees together with her feet apart",
    "knees_up": "with her knees raised",
    "looking_at_viewer": "looking toward the viewer",
    "smile": "smiling",
    "tongue_out": "showing her tongue",
}

OBJECT_TAGS = {
    "bag": "a bag",
    "balloon": "a balloon",
    "bottle": "a bottle",
    "heart_balloon": "a heart-shaped balloon",
}

SCENE_TAGS = {
    "building": "buildings",
    "car": "cars",
    "city": "a city",
    "cityscape": "a cityscape",
    "convenience_store": "a convenience store",
    "lamppost": "lampposts",
    "motor_vehicle": "vehicles",
    "night_sky": "a night sky",
    "sky": "the sky",
}

STYLE_TAGS = {
    "photorealistic": "a photorealistic style",
    "realistic": "a realistic style",
}

HAIR_COLORS = {
    "black_hair": "black",
    "blonde_hair": "blonde",
    "brown_hair": "brown",
    "pink_hair": "pink",
    "red_hair": "red",
    "white_hair": "white",
}

HAIR_LENGTHS = {
    "long_hair": "long",
    "medium_hair": "medium-length",
    "short_hair": "short",
}


def _join(items: list[str]) -> str:
    if len(items) < 2:
        return "".join(items)
    if len(items) == 2:
        return " and ".join(items)
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _tag_scores(
    items: list[dict[str, object]],
    threshold: float,
) -> dict[str, float]:
    selected: dict[str, float] = {}
    for item in items:
        tag = str(item["tag"])
        score = float(item["score"])
        if score >= threshold:
            selected[tag] = score
    return selected


def _collect(
    tags: set[str],
    phrases: dict[str, str],
    consumed: set[str],
) -> list[str]:
    result = []
    for tag, phrase in phrases.items():
        if tag in tags:
            consumed.add(tag)
            result.append(phrase)
    return result


def _remove_redundant_tags(tags: set[str]) -> None:
    replacements = {
        "black_choker": {"choker"},
        "brown_shorts": {"shorts"},
        "cityscape": {"city"},
        "double_bun": {"hair_bun"},
        "heart_balloon": {"balloon"},
        "large_breasts": {"breasts", "medium_breasts", "small_breasts"},
        "medium_breasts": {"breasts"},
        "photorealistic": {"realistic"},
        "pink_cardigan": {"cardigan"},
        "round_eyewear": {"glasses"},
        "small_breasts": {"breasts"},
        "white_dress": {"dress"},
    }
    for specific, general in replacements.items():
        if specific in tags:
            tags.difference_update(general)

    if "topless" in tags:
        tags.difference_update({"bikini", "swimsuit"})
    if "panties" in tags:
        tags.discard("underwear")
    if "car" in tags:
        tags.discard("motor_vehicle")
    if "tongue_out" in tags:
        tags.discard("tongue")
    if "holding_balloon" in tags or "holding_bottle" in tags:
        tags.discard("holding")


def build_faithful_prompt(
    general: list[dict[str, object]],
    character: list[dict[str, object]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, object]:
    """Convert sufficiently confident WD tags into conservative prose."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    scores = _tag_scores(general, threshold)
    character_names = [
        str(item["tag"]).replace("_", " ").title() for item in character
    ]
    tags = set(scores)
    _remove_redundant_tags(tags)
    consumed: set[str] = set()

    female = "1girl" in tags
    male = "1boy" in tags
    solo = "solo" in tags
    consumed.update({"1girl", "1boy", "solo"} & tags)
    if character_names:
        subject = _join(character_names)
    elif female:
        subject = "one female subject"
    elif male:
        subject = "one male subject"
    else:
        subject = "the main subject"
    if solo:
        subject += " alone"
    sentences = [f"The image shows {subject}."]
    pronoun = "She" if female else "He" if male else "The subject"

    hair_color = next(
        (phrase for tag, phrase in HAIR_COLORS.items() if tag in tags),
        None,
    )
    hair_length = next(
        (phrase for tag, phrase in HAIR_LENGTHS.items() if tag in tags),
        None,
    )
    consumed.update(tag for tag in HAIR_COLORS if tag in tags)
    consumed.update(tag for tag in HAIR_LENGTHS if tag in tags)
    appearance = _collect(tags, APPEARANCE_TAGS, consumed)
    if hair_color or hair_length:
        appearance.insert(
            0,
            " ".join(part for part in (hair_length, hair_color, "hair") if part),
        )
    if appearance:
        sentences.append(f"{pronoun} has {_join(appearance)}.")

    clothing = _collect(tags, CLOTHING_TAGS, consumed)
    if "pink_cardigan" in tags:
        clothing.append("a pink cardigan")
        consumed.add("pink_cardigan")
    topless = "topless" in tags
    consumed.add("topless")
    if topless and clothing:
        sentences.append(f"{pronoun} is topless and wearing {_join(clothing)}.")
    elif topless:
        sentences.append(f"{pronoun} is topless.")
    elif clothing:
        sentences.append(f"{pronoun} is wearing {_join(clothing)}.")

    actions: list[str] = []
    for posture in ("standing", "sitting"):
        if posture in tags:
            actions.append(posture)
            consumed.add(posture)
    if "barefoot" in tags:
        actions.append("barefoot")
        consumed.add("barefoot")
    if "holding_balloon" in tags:
        held = (
            "a heart-shaped balloon"
            if "heart_balloon" in tags
            else "a balloon"
        )
        actions.append(f"holding {held}")
        consumed.update({"holding_balloon", "heart_balloon", "balloon"} & tags)
    if "holding_bottle" in tags:
        if "drinking" in tags:
            actions.append("holding and drinking from a bottle")
            consumed.add("drinking")
        else:
            actions.append("holding a bottle")
        consumed.update({"holding_bottle", "bottle"} & tags)
    actions.extend(_collect(tags - consumed, ACTION_TAGS, consumed))
    if actions:
        sentences.append(f"{pronoun} is {_join(actions)}.")

    objects = _collect(tags - consumed, OBJECT_TAGS, consumed)
    if objects:
        sentences.append(f"Visible objects include {_join(objects)}.")

    scene_parts: list[str] = []
    if "outdoors" in tags:
        scene_parts.append("outdoors")
        consumed.add("outdoors")
    if "rain" in tags:
        scene_parts.append("in the rain")
        consumed.add("rain")
    if "night" in tags:
        scene_parts.append("at night")
        consumed.add("night")
    background = _collect(tags, SCENE_TAGS, consumed)
    if scene_parts or background:
        scene = " ".join(scene_parts) or "a visible setting"
        if background:
            scene += f", with {_join(background)}"
        sentences.append(f"The scene is {scene}.")

    if "full_body" in tags:
        sentences.append("The composition shows the full body.")
        consumed.add("full_body")

    wet = "wet" in tags
    blood = "blood" in tags
    consumed.update({"wet", "blood"} & tags)
    if wet and blood:
        sentences.append("The subject is wet, with visible blood.")
    elif wet:
        sentences.append("The subject is wet.")
    elif blood:
        sentences.append("Visible blood is present.")

    if "navel" in tags:
        sentences.append("The navel is visible.")
        consumed.add("navel")

    styles = _collect(tags, STYLE_TAGS, consumed)
    if styles:
        sentences.append(f"The image has {_join(styles)}.")

    consumed.update(EXCLUDED_TAGS & tags)
    remaining = sorted(tags - consumed)
    if remaining:
        details = [tag.replace("_", " ") for tag in remaining]
        sentences.append(f"Additional visible details: {_join(details)}.")

    supporting_tags = [
        {"tag": tag, "score": scores[tag]}
        for tag in sorted(tags, key=lambda tag: scores[tag], reverse=True)
    ]
    return {
        "threshold": threshold,
        "supporting_tags": supporting_tags,
        "character_tags": character_names,
        "prompt": " ".join(sentences),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--general-threshold", type=float, default=0.35)
    parser.add_argument("--character-threshold", type=float, default=0.85)
    parser.add_argument("--faithful-threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    for value, name in (
        (args.general_threshold, "--general-threshold"),
        (args.character_threshold, "--character-threshold"),
        (args.faithful_threshold, "--faithful-threshold"),
    ):
        if not 0 <= value <= 1:
            parser.error(f"{name} must be between 0 and 1")

    try:
        danbooru = predict(
            args.image,
            args.model_dir,
            general_threshold=args.general_threshold,
            character_threshold=args.character_threshold,
        )
        result = build_faithful_prompt(
            danbooru["general"],
            danbooru["character"],
            threshold=args.faithful_threshold,
        )
    except (FileNotFoundError, ImageInputError, ValueError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {"input": str(args.image.resolve()), **result},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
