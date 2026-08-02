"""Generate a Florence-2 reference caption with local ONNX models."""

from __future__ import annotations

import argparse
import json
import os
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
from transformers import AutoImageProcessor, AutoTokenizer

from .image_processing import ImageInputError, prepare_image

DEFAULT_MODEL_DIR = Path(
    "models/transformers-js-cache/onnx-community/Florence-2-base-ft"
)
MODEL_ID = "onnx-community/Florence-2-base-ft"
MODEL_REVISION = "fac887a509cb8264d5639f04674c04977c65d937"
TASK_PROMPT = "Describe in detail what is shown in the image."
MAX_NEW_TOKENS = 512


def _require_model_files(model_dir: Path) -> tuple[Path, Path, Path, Path]:
    paths = (
        model_dir / "onnx/vision_encoder.onnx",
        model_dir / "onnx/embed_tokens_int8.onnx",
        model_dir / "onnx/encoder_model_int8.onnx",
        model_dir / "onnx/decoder_model_merged_int8.onnx",
    )
    if not all(path.is_file() for path in paths):
        raise FileNotFoundError(
            f"Florence-2 ONNX files not found in {model_dir}. "
            "See README.md for the download command."
        )
    return paths


@lru_cache(maxsize=1)
def _load_model(model_dir: Path):
    paths = _require_model_files(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    processor = AutoImageProcessor.from_pretrained(
        model_dir,
        local_files_only=True,
        use_fast=False,
    )
    sessions = [
        ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        for path in paths
    ]
    return tokenizer, processor, *sessions


def _initial_past(decoder_session) -> dict[str, np.ndarray]:
    return {
        item.name: np.zeros((1, 12, 0, 64), dtype=np.float32)
        for item in decoder_session.get_inputs()
        if item.name.startswith("past_key_values.")
    }


def _updated_past(
    previous: dict[str, np.ndarray],
    output_names: list[str],
    outputs: list[np.ndarray],
) -> dict[str, np.ndarray]:
    updated = previous.copy()
    for output_name, value in zip(output_names, outputs):
        name = output_name.replace("present.", "past_key_values.")
        if ".encoder." in name and previous[name].shape[2]:
            continue
        updated[name] = value
    return updated


def _generate(
    embed_session,
    decoder_session,
    encoder_hidden: np.ndarray,
    attention_mask: np.ndarray,
    *,
    max_new_tokens: int,
) -> np.ndarray:
    past = _initial_past(decoder_session)
    token = np.array([[2]], dtype=np.int64)
    generated: list[int] = []
    output_names = [item.name for item in decoder_session.get_outputs()[1:]]

    for step in range(max_new_tokens):
        logits, *present = decoder_session.run(
            None,
            {
                "encoder_attention_mask": attention_mask,
                "encoder_hidden_states": encoder_hidden,
                "inputs_embeds": embed_session.run(
                    None,
                    {"input_ids": token},
                )[0],
                "use_cache_branch": np.array([step > 0]),
                **past,
            },
        )
        next_id = 0 if step == 0 else int(logits[0, -1].argmax())
        if next_id == 2:
            break
        generated.append(next_id)
        token = np.array([[next_id]], dtype=np.int64)
        past = _updated_past(past, output_names, present)

    return np.array([generated], dtype=np.int64)


def caption(
    image_path: Path,
    model_dir: Path = DEFAULT_MODEL_DIR,
    *,
    max_new_tokens: int = MAX_NEW_TOKENS,
) -> dict[str, object]:
    (
        tokenizer,
        processor,
        vision_session,
        embed_session,
        encoder_session,
        decoder_session,
    ) = _load_model(model_dir)

    image = prepare_image(image_path, size=768).image
    text = tokenizer(TASK_PROMPT, return_tensors="np")
    pixels = processor(images=image, return_tensors="np")["pixel_values"]

    started = time.perf_counter()
    image_features = vision_session.run(None, {"pixel_values": pixels})[0]
    text_features = embed_session.run(
        None,
        {"input_ids": text["input_ids"]},
    )[0]
    inputs_embeds = np.concatenate([image_features, text_features], axis=1)
    attention_mask = np.concatenate(
        [
            np.ones(image_features.shape[:2], dtype=np.int64),
            text["attention_mask"],
        ],
        axis=1,
    )
    encoder_hidden = encoder_session.run(
        None,
        {
            "inputs_embeds": inputs_embeds,
            "attention_mask": attention_mask,
        },
    )[0]
    generated_tokens = _generate(
        embed_session,
        decoder_session,
        encoder_hidden,
        attention_mask,
        max_new_tokens=max_new_tokens,
    )
    prompt = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
    )[0].strip()
    return {
        "input": str(image_path.resolve()),
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "task": "detailed_caption",
        "provider": decoder_session.get_providers()[0],
        "generation_seconds": time.perf_counter() - started,
        "generated_tokens": generated_tokens.shape[1],
        "prompt": prompt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    args = parser.parse_args()
    if not 1 <= args.max_new_tokens <= MAX_NEW_TOKENS:
        parser.error(f"--max-new-tokens must be between 1 and {MAX_NEW_TOKENS}")

    try:
        result = caption(
            args.image,
            args.model_dir,
            max_new_tokens=args.max_new_tokens,
        )
    except (FileNotFoundError, ImageInputError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
