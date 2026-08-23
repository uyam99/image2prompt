"""Compose the optional editable Florence-first prompt."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STYLE_PREFIXES = (
    ("Anime-style drawing of ", "anime-style illustration"),
    ("Digital illustration of ", "digital illustration"),
    ("Photo of ", "photorealistic photograph"),
)
DROP_SENTENCES = re.compile(
    r"\b(overall mood|atmosphere|high quality|watermark)\b",
    re.IGNORECASE,
)
DEMOGRAPHICS = re.compile(r"\b(Asian|Japanese|Korean|Chinese)\s+", re.IGNORECASE)
EXACT_AGE = re.compile(
    r"\b(?:a\s+)?\d{1,2}(?:-year-old|\s+years?\s+old)\s+",
    re.IGNORECASE,
)


def _clean_sentence(sentence: str) -> str:
    sentence = DEMOGRAPHICS.sub("", sentence)
    sentence = EXACT_AGE.sub("", sentence)
    sentence = re.sub(
        r"\byoung (?:girl|woman)\b",
        "young adult woman",
        sentence,
        flags=re.IGNORECASE,
    )
    sentence = re.sub(
        r"\ba girl\b",
        "a young adult woman",
        sentence,
        flags=re.IGNORECASE,
    )
    sentence = re.sub(
        r",?\s+(?:creating|adding to)\s+[^.]*\batmosphere\b[^.]*",
        "",
        sentence,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", sentence).strip(" ,")


def split_florence_prompt(caption: str, detailed: str) -> tuple[str, str]:
    """Return editable content and a separately editable style hint."""
    style = ""
    for prefix, hint in STYLE_PREFIXES:
        if detailed.startswith(prefix):
            detailed = detailed.removeprefix(prefix)
            style = hint
            break

    sentences = []
    for sentence in re.split(r"(?<=[.!?])\s+", detailed.strip()):
        if sentence and not DROP_SENTENCES.search(sentence):
            cleaned = _clean_sentence(sentence)
            if cleaned:
                sentences.append(cleaned.rstrip(".") + ".")
    short = _clean_sentence(caption).rstrip(".")
    content = " ".join(([short + "."] if short else []) + sentences)
    return content, style


def compose_prompt(content: str, style: str, wd: str, camera: str) -> str:
    """Join user-editable layers without rewriting or deduplicating them."""
    return "\n\n".join(part.strip() for part in (content, style, wd, camera) if part.strip())


def _resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def _data_dir() -> Path:
    override = os.environ.get("IMAGE2PROMPT_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "image2prompt"
    return Path.home() / "Library" / "Application Support" / "image2prompt"


def _uv_path() -> Path:
    override = os.environ.get("IMAGE2PROMPT_UV")
    bundled = _resource_root() / "bin" / ("uv.exe" if sys.platform == "win32" else "uv")
    found = override or (str(bundled) if bundled.is_file() else shutil.which("uv"))
    if not found or not Path(found).is_file():
        raise FileNotFoundError("自然言語機能の実行ファイル（uv）が見つかりません。")
    return Path(found)


def _local_model_dir() -> Path | None:
    override = os.environ.get("IMAGE2PROMPT_FLORENCE_MODEL_DIR")
    candidate = Path(override) if override else _resource_root() / "models/florence-2-large-promptgen-v2"
    return candidate if (candidate / "model.safetensors").is_file() else None


def generate_florence_layers(image_path: Path) -> tuple[str, str, float]:
    """Run the isolated PromptGen environment and return content/style/time."""
    root = _resource_root()
    script = root / "image2prompt/florence_runner.py"
    if not script.is_file():
        raise FileNotFoundError("自然言語機能の推論スクリプトが見つかりません。")
    data_dir = _data_dir()
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "prompt.json"
        env = os.environ.copy()
        env.setdefault("UV_CACHE_DIR", str(data_dir / "uv"))
        env.setdefault("HF_HOME", str(data_dir / "huggingface"))
        env.setdefault("HF_MODULES_CACHE", str(data_dir / "huggingface/modules"))
        command = [
            str(_uv_path()),
            "run",
            "--script",
            str(script),
            str(image_path),
            "--output",
            str(output),
        ]
        model_dir = _local_model_dir()
        if model_dir:
            command.extend(("--model-dir", str(model_dir)))
        try:
            subprocess.run(
                command,
                cwd=root,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                timeout=3600,
            )
        except subprocess.CalledProcessError as error:
            details = (error.stderr or error.stdout or str(error)).strip()
            raise RuntimeError(details[-1200:]) from error
        result = json.loads(output.read_text(encoding="utf-8"))
    item = result["images"][0]["results"]
    content, style = split_florence_prompt(
        item["caption"]["output"]["<CAPTION>"],
        item["detailed"]["output"]["<DETAILED_CAPTION>"],
    )
    seconds = float(result["load_seconds"])
    seconds += float(item["caption"]["seconds"])
    seconds += float(item["detailed"]["seconds"])
    return content, style, seconds
