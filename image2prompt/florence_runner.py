# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#   "einops>=0.8,<1",
#   "huggingface-hub==0.36.2",
#   "numpy<2",
#   "Pillow>=11,<12",
#   "timm==1.0.9",
#   "torch==2.2.2",
#   "torchvision==0.17.2",
#   "transformers==4.49.0",
# ]
# ///

"""Generate the two Florence captions used by the optional natural-language UI."""

import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

MODEL = "MiaoshouAI/Florence-2-large-PromptGen-v2.0"
REVISION = "4aa33eaf50aab040fe8523312ff52eb53322c220"
TASKS = ("<CAPTION>", "<DETAILED_CAPTION>")


def load_model(model_dir: Path | None):
    source = str(model_dir) if model_dir else MODEL
    options = {"local_files_only": True} if model_dir else {"revision": REVISION}
    model = AutoModelForCausalLM.from_pretrained(
        source,
        attn_implementation="eager",
        trust_remote_code=True,
        **options,
    ).eval()
    processor = AutoProcessor.from_pretrained(
        source,
        trust_remote_code=True,
        **options,
    )
    return model, processor


def generate(model, processor, image: Image.Image, task: str) -> dict[str, object]:
    inputs = processor(text=task, images=image, return_tensors="pt")
    started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=512,
            do_sample=False,
            num_beams=3,
        )
    text = processor.batch_decode(generated, skip_special_tokens=False)[0]
    return {
        "seconds": time.perf_counter() - started,
        "output": processor.post_process_generation(
            text,
            task=task,
            image_size=image.size,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ready-file", type=Path)
    args = parser.parse_args()

    started = time.perf_counter()
    model, processor = load_model(args.model_dir)
    load_seconds = time.perf_counter() - started
    if args.ready_file:
        args.ready_file.touch()
    with Image.open(args.image) as source:
        image = source.convert("RGB")
    results = {
        "caption": generate(model, processor, image, TASKS[0]),
        "detailed": generate(model, processor, image, TASKS[1]),
    }
    payload = {
        "model": str(args.model_dir) if args.model_dir else MODEL,
        "revision": None if args.model_dir else REVISION,
        "load_seconds": load_seconds,
        "images": [{"input": str(args.image.resolve()), "results": results}],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
