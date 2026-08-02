"""Launch the bundled desktop app."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    if getattr(sys, "frozen", False):
        os.environ.setdefault(
            "IMAGE2PROMPT_TAG_MODEL_DIR",
            str(Path(sys._MEIPASS) / "models/wd-swinv2-tagger-v3"),
        )
    from image2prompt.desktop import main as run

    run()


if __name__ == "__main__":
    main()
