"""Generate Danbooru tags with WD SwinV2 Tagger v3."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort

from .image_processing import ImageInputError, prepare_image

DEFAULT_MODEL_DIR = Path("models/wd-swinv2-tagger-v3")
MODEL_REVISION = "627aef95638667ddcaa3ac8ae625e88ea5b02f51"


def _load_labels(path: Path) -> tuple[list[str], list[int]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    try:
        return (
            [row["name"] for row in rows],
            [int(row["category"]) for row in rows],
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Invalid tag table: {path}") from exc


def _select_tags(
    names: list[str],
    categories: list[int],
    scores: np.ndarray,
    general_threshold: float,
    character_threshold: float,
) -> dict[str, object]:
    if len(names) != len(categories) or len(names) != len(scores):
        raise ValueError("Model output and tag table have different lengths")

    tagged = list(zip(names, categories, map(float, scores), strict=True))
    ratings = [item for item in tagged if item[1] == 9]
    if not ratings:
        raise ValueError("Tag table has no rating labels")

    rating = max(ratings, key=lambda item: item[2])
    general = sorted(
        (
            (name, score)
            for name, category, score in tagged
            if category == 0 and score > general_threshold
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    character = sorted(
        (
            (name, score)
            for name, category, score in tagged
            if category == 4 and score > character_threshold
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return {
        "rating": {"tag": rating[0], "score": rating[2]},
        "general": [{"tag": name, "score": score} for name, score in general],
        "character": [{"tag": name, "score": score} for name, score in character],
        "prompt": ", ".join(
            name
            for name, _ in sorted(
                general + character,
                key=lambda item: item[1],
                reverse=True,
            )
        ),
    }


def predict(
    image_path: Path,
    model_dir: Path = DEFAULT_MODEL_DIR,
    *,
    general_threshold: float = 0.35,
    character_threshold: float = 0.85,
) -> dict[str, object]:
    model_path = model_dir / "model.onnx"
    labels_path = model_dir / "selected_tags.csv"
    if not model_path.is_file() or not labels_path.is_file():
        raise FileNotFoundError(
            f"Model files not found in {model_dir}. See README.md for the download command."
        )

    session = ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"],
    )
    model_input = session.get_inputs()[0]
    model_output = session.get_outputs()[0]
    target_size = int(model_input.shape[1])
    prepared = prepare_image(image_path, size=target_size)
    image_array = np.ascontiguousarray(
        np.asarray(prepared.image, dtype=np.float32)[:, :, ::-1][None, ...]
    )

    started = time.perf_counter()
    scores = session.run([model_output.name], {model_input.name: image_array})[0][0]
    elapsed = time.perf_counter() - started
    names, categories = _load_labels(labels_path)
    result = _select_tags(
        names,
        categories,
        scores,
        general_threshold,
        character_threshold,
    )
    return {
        "input": str(image_path.resolve()),
        "model": "SmilingWolf/wd-swinv2-tagger-v3",
        "model_revision": MODEL_REVISION,
        "provider": session.get_providers()[0],
        "inference_seconds": elapsed,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--general-threshold", type=float, default=0.35)
    parser.add_argument("--character-threshold", type=float, default=0.85)
    args = parser.parse_args()

    for value, name in (
        (args.general_threshold, "--general-threshold"),
        (args.character_threshold, "--character-threshold"),
    ):
        if not 0 <= value <= 1:
            parser.error(f"{name} must be between 0 and 1")

    try:
        result = predict(
            args.image,
            args.model_dir,
            general_threshold=args.general_threshold,
            character_threshold=args.character_threshold,
        )
    except (FileNotFoundError, ImageInputError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
