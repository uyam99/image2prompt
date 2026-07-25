"""Generate a concise English image prompt with SmolVLM ONNX."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
from transformers import AutoConfig, AutoProcessor  # noqa: E402

from .image_processing import ImageInputError, prepare_image

DEFAULT_MODEL_DIR = Path("models/smolvlm-256m-instruct")
MODEL_REVISION = "7e3e67edbbed1bf9888184d9df282b700a323964"
INSTRUCTION = (
    "Write one English image-generation prompt under 35 words. "
    "Describe only clearly visible subjects, clothing, action, setting, lighting, "
    "and style. Do not name brands or artists."
)


def _require_model_files(model_dir: Path) -> tuple[Path, Path, Path]:
    paths = (
        model_dir / "onnx/vision_encoder.onnx",
        model_dir / "onnx/embed_tokens_int8.onnx",
        model_dir / "onnx/decoder_model_merged_int8.onnx",
    )
    if not all(path.is_file() for path in paths):
        raise FileNotFoundError(
            f"SmolVLM ONNX files not found in {model_dir}. "
            "See README.md for the download command."
        )
    return paths


def _extend_attention_mask(
    attention_mask: np.ndarray,
    input_ids: np.ndarray,
) -> np.ndarray:
    return np.concatenate(
        [attention_mask, np.ones_like(input_ids)],
        axis=-1,
    )


def caption(
    image_path: Path,
    model_dir: Path = DEFAULT_MODEL_DIR,
    *,
    max_new_tokens: int = 64,
) -> dict[str, object]:
    vision_path, embed_path, decoder_path = _require_model_files(model_dir)
    config = AutoConfig.from_pretrained(model_dir, local_files_only=True)
    processor = AutoProcessor.from_pretrained(
        model_dir,
        local_files_only=True,
        size={"longest_edge": 512},
    )
    sessions = [
        ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        for path in (vision_path, embed_path, decoder_path)
    ]
    vision_session, embed_session, decoder_session = sessions

    # ponytail: reuse square input; restore original aspect if layout quality suffers.
    image = prepare_image(image_path, size=512).image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": INSTRUCTION},
            ],
        }
    ]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="np")

    text_config = config.text_config
    batch_size = inputs["input_ids"].shape[0]
    past_key_values = {
        f"past_key_values.{layer}.{key}": np.zeros(
            [
                batch_size,
                text_config.num_key_value_heads,
                0,
                text_config.head_dim,
            ],
            dtype=np.float32,
        )
        for layer in range(text_config.num_hidden_layers)
        for key in ("key", "value")
    }
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    position_ids = np.cumsum(attention_mask, axis=-1)
    generated_tokens = np.empty((batch_size, 0), dtype=np.int64)
    image_features = None

    started = time.perf_counter()
    for _ in range(max_new_tokens):
        inputs_embeds = embed_session.run(None, {"input_ids": input_ids})[0]
        if image_features is None:
            image_features = vision_session.run(
                ["image_features"],
                {
                    "pixel_values": inputs["pixel_values"],
                    "pixel_attention_mask": inputs["pixel_attention_mask"].astype(
                        np.bool_
                    ),
                },
            )[0]
            inputs_embeds[inputs["input_ids"] == config.image_token_id] = (
                image_features.reshape(-1, image_features.shape[-1])
            )

        logits, *present_key_values = decoder_session.run(
            None,
            {
                "inputs_embeds": inputs_embeds,
                "attention_mask": attention_mask,
                "position_ids": position_ids,
                **past_key_values,
            },
        )
        input_ids = logits[:, -1].argmax(-1, keepdims=True)
        generated_tokens = np.concatenate(
            [generated_tokens, input_ids],
            axis=-1,
        )
        if (input_ids == text_config.eos_token_id).all():
            break

        attention_mask = _extend_attention_mask(attention_mask, input_ids)
        position_ids = position_ids[:, -1:] + 1
        for index, key in enumerate(past_key_values):
            past_key_values[key] = present_key_values[index]

    generated = processor.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
    )[0].strip()
    return {
        "input": str(image_path.resolve()),
        "model": "HuggingFaceTB/SmolVLM-256M-Instruct",
        "model_revision": MODEL_REVISION,
        "provider": decoder_session.get_providers()[0],
        "generation_seconds": time.perf_counter() - started,
        "generated_tokens": generated_tokens.shape[1],
        "prompt": generated,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.max_new_tokens <= 256:
        parser.error("--max-new-tokens must be between 1 and 256")

    try:
        result = caption(
            args.image,
            args.model_dir,
            max_new_tokens=args.max_new_tokens,
        )
    except (FileNotFoundError, ImageInputError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
