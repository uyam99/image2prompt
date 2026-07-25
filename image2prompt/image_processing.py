"""Load and normalize images for model inference."""

from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF"})
DEFAULT_MAX_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_PIXELS = 40_000_000


class ImageInputError(ValueError):
    """An image cannot be safely processed."""


@dataclass(frozen=True)
class PreparedImage:
    image: Image.Image
    source_format: str
    original_size: tuple[int, int]
    oriented_size: tuple[int, int]


def _as_rgb(image: Image.Image) -> Image.Image:
    if "A" not in image.getbands() and "transparency" not in image.info:
        return image.convert("RGB")
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, "white")
    background.alpha_composite(rgba)
    return background.convert("RGB")


def prepare_image(
    path: str | Path,
    *,
    size: int = 448,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> PreparedImage:
    """Load the first frame, apply orientation, and fit it on a white square."""
    source_path = Path(path)
    if size <= 0:
        raise ValueError("size must be greater than zero")
    if not source_path.is_file():
        raise ImageInputError(f"File not found: {source_path}")
    if source_path.stat().st_size > max_bytes:
        raise ImageInputError(f"File exceeds {max_bytes} bytes: {source_path}")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source_path) as source:
                source_format = source.format or ""
                if source_format not in SUPPORTED_FORMATS:
                    raise ImageInputError(
                        f"Unsupported image format '{source_format or 'unknown'}': {source_path}"
                    )
                original_size = source.size
                if original_size[0] * original_size[1] > max_pixels:
                    raise ImageInputError(
                        f"Image exceeds {max_pixels} pixels: {source_path}"
                    )
                source.seek(0)
                oriented = ImageOps.exif_transpose(source)
                oriented.load()
                oriented_size = oriented.size
                rgb = _as_rgb(oriented)
    except ImageInputError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise ImageInputError(f"Cannot read image '{source_path}': {exc}") from exc

    resized = ImageOps.contain(rgb, (size, size), Image.Resampling.LANCZOS)
    prepared = Image.new("RGB", (size, size), "white")
    prepared.paste(
        resized,
        ((size - resized.width) // 2, (size - resized.height) // 2),
    )
    return PreparedImage(prepared, source_format, original_size, oriented_size)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize an image and save a model-input preview."
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("--size", type=int, default=448)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-megapixels", type=float, default=40)
    args = parser.parse_args()

    try:
        result = prepare_image(
            args.image,
            size=args.size,
            max_pixels=int(args.max_megapixels * 1_000_000),
        )
    except (ImageInputError, ValueError) as exc:
        parser.error(str(exc))

    output = args.output or Path("outputs") / f"{args.image.stem}.prepared.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(output)
    print(
        json.dumps(
            {
                "input": str(args.image.resolve()),
                "source_format": result.source_format,
                "original_size": result.original_size,
                "oriented_size": result.oriented_size,
                "processed_mode": result.image.mode,
                "processed_size": result.image.size,
                "output": str(output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
