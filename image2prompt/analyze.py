"""Generate Danbooru and natural-language prompts for one image."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .faithful_prompt import build_faithful_prompt
from .image_processing import ImageInputError
from .smolvlm_caption import DEFAULT_MODEL_DIR as CAPTION_MODEL_DIR
from .smolvlm_caption import caption
from .wd_tagger import DEFAULT_MODEL_DIR as TAG_MODEL_DIR
from .wd_tagger import predict


def analyze(
    image_path: Path,
    *,
    tag_model_dir: Path = TAG_MODEL_DIR,
    caption_model_dir: Path = CAPTION_MODEL_DIR,
    general_threshold: float = 0.35,
    character_threshold: float = 0.85,
    max_new_tokens: int = 128,
) -> dict[str, object]:
    started = time.perf_counter()
    danbooru = predict(
        image_path,
        tag_model_dir,
        general_threshold=general_threshold,
        character_threshold=character_threshold,
    )
    faithful_prompt = build_faithful_prompt(
        danbooru["general"],
        danbooru["character"],
    )
    natural_language = caption(
        image_path,
        caption_model_dir,
        max_new_tokens=max_new_tokens,
    )
    danbooru.pop("input")
    natural_language.pop("input")
    return {
        "input": str(image_path.resolve()),
        "total_seconds": time.perf_counter() - started,
        "danbooru": danbooru,
        "faithful_prompt": faithful_prompt,
        "natural_language": natural_language,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--tag-model-dir", type=Path, default=TAG_MODEL_DIR)
    parser.add_argument("--caption-model-dir", type=Path, default=CAPTION_MODEL_DIR)
    parser.add_argument("--general-threshold", type=float, default=0.35)
    parser.add_argument("--character-threshold", type=float, default=0.85)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    args = parser.parse_args()

    for value, name in (
        (args.general_threshold, "--general-threshold"),
        (args.character_threshold, "--character-threshold"),
    ):
        if not 0 <= value <= 1:
            parser.error(f"{name} must be between 0 and 1")
    if not 1 <= args.max_new_tokens <= 500:
        parser.error("--max-new-tokens must be between 1 and 500")

    try:
        result = analyze(
            args.image,
            tag_model_dir=args.tag_model_dir,
            caption_model_dir=args.caption_model_dir,
            general_threshold=args.general_threshold,
            character_threshold=args.character_threshold,
            max_new_tokens=args.max_new_tokens,
        )
    except (FileNotFoundError, ImageInputError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
