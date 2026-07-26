"""Local Gradio UI for image2prompt."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import gradio as gr

from .analyze import analyze
from .faithful_prompt import (
    DEFAULT_ENVIRONMENT_PRESET,
    ENVIRONMENT_PRESET_CHOICES,
    ENVIRONMENT_PRESETS,
)
from .image_processing import ImageInputError, prepare_image

IMAGE_SUFFIXES = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
)
IMAGE_KINDS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WebP",
    ".bmp": "BMP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".gif": "GIF",
}
FOLDER_SORT_CHOICES = [
    ("名前", "name"),
    ("更新日", "modified"),
    ("種類", "kind"),
]
FOLDER_SORT_LABELS = {value: label for label, value in FOLDER_SORT_CHOICES}
SORT_DIRECTION_CHOICES = [
    ("昇順", "ascending"),
    ("降順", "descending"),
]
SORT_DIRECTION_LABELS = {
    value: label for label, value in SORT_DIRECTION_CHOICES
}
SETTINGS_PATH = (
    Path.home() / "Library" / "Application Support" / "image2prompt" / "settings.json"
)
DEFAULT_SETTINGS: dict[str, float | str] = {
    "general_threshold": 0.35,
    "character_threshold": 0.85,
    "environment_preset": DEFAULT_ENVIRONMENT_PRESET,
}
TOKEN_REFERENCE = 512
THUMBNAIL_SIZE = 384
THUMBNAIL_DIR = Path(tempfile.gettempdir()) / "image2prompt-thumbnails"
FINDER_SORT_SCRIPT = """
ObjC.import("Foundation");
const data = $.NSFileHandle.fileHandleWithStandardInput.readDataToEndOfFile;
const text = ObjC.unwrap(
    $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding)
);
const names = JSON.parse(text);
names.sort((a, b) =>
    $.NSString.stringWithString(a).localizedStandardCompare(
        $.NSString.stringWithString(b)
    )
);
JSON.stringify(names);
"""


def estimate_prompt_tokens(prompt: str) -> int:
    """Return a model-independent English prompt token estimate."""
    return (len(prompt) + 3) // 4


def token_status(prompt: str) -> str:
    count = estimate_prompt_tokens(prompt)
    return (
        f"概算トークン数：**{count}** / 基準：**{TOKEN_REFERENCE}**"
        "（超過可・実数は使用モデルで変動）"
    )


def _validated_settings(
    general_threshold: object,
    character_threshold: object,
    environment_preset: object,
) -> dict[str, float | str]:
    general = float(general_threshold)
    character = float(character_threshold)
    preset = str(environment_preset)
    if not 0 <= general <= 1 or not 0 <= character <= 1:
        raise ValueError("設定値が許容範囲外です。")
    if preset not in ENVIRONMENT_PRESETS:
        raise ValueError("環境プリセットが不正です。")
    return {
        "general_threshold": general,
        "character_threshold": character,
        "environment_preset": preset,
    }


def load_settings(path: Path = SETTINGS_PATH) -> dict[str, float | str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _validated_settings(
            data["general_threshold"],
            data["character_threshold"],
            data.get("environment_preset", DEFAULT_ENVIRONMENT_PRESET),
        )
    except (KeyError, OSError, TypeError, ValueError):
        return DEFAULT_SETTINGS.copy()


def save_settings(
    general_threshold: float,
    character_threshold: float,
    environment_preset: str,
    path: Path = SETTINGS_PATH,
) -> str:
    try:
        settings = _validated_settings(
            general_threshold,
            character_threshold,
            environment_preset,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except (OSError, ValueError) as error:
        raise gr.Error(f"解析設定を保存できませんでした：{error}") from error
    return "解析設定を保存しました。"


def _natural_name_key(path: Path) -> tuple[tuple[int, str | int], ...]:
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", path.name)
    )


def _finder_sorted_paths(paths: list[Path]) -> list[Path]:
    fallback = sorted(paths, key=_natural_name_key)
    if sys.platform != "darwin" or len(paths) < 2:
        return fallback
    try:
        result = subprocess.run(
            [
                "osascript",
                "-l",
                "JavaScript",
                "-e",
                FINDER_SORT_SCRIPT,
            ],
            input=json.dumps([path.name for path in paths], ensure_ascii=False),
            capture_output=True,
            text=True,
            check=False,
        )
        names = json.loads(result.stdout) if not result.returncode else []
        by_name = {path.name: path for path in paths}
        if len(names) == len(paths) and set(names) == set(by_name):
            return [by_name[name] for name in names]
    except (OSError, TypeError, ValueError):
        pass
    return fallback


def _sort_folder_images(
    paths: list[Path],
    sort_by: str,
    direction: str,
) -> list[Path]:
    if direction not in {"ascending", "descending"}:
        raise gr.Error("昇順または降順を選択してください。")
    if sort_by == "name":
        ordered = _finder_sorted_paths(paths)
        return list(reversed(ordered)) if direction == "descending" else ordered
    elif sort_by == "modified":
        key = lambda path: (path.stat().st_mtime, _natural_name_key(path))
    elif sort_by == "kind":
        key = lambda path: (
            IMAGE_KINDS[path.suffix.casefold()].casefold(),
            _natural_name_key(path),
        )
    else:
        raise gr.Error("並び順を選択できませんでした。")
    return sorted(paths, key=key, reverse=direction == "descending")


def _thumbnail_path(source: Path) -> str:
    stat = source.stat()
    cache_key = hashlib.sha256(
        f"{source.resolve()}\0{stat.st_mtime_ns}\0{stat.st_size}".encode()
    ).hexdigest()
    destination = THUMBNAIL_DIR / f"{cache_key}.jpg"
    if not destination.is_file():
        THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        prepare_image(source, size=THUMBNAIL_SIZE).image.save(
            temporary,
            format="JPEG",
            quality=85,
        )
        temporary.replace(destination)
    return str(destination)


def load_folder(
    folder_path: str | None,
    sort_by: str,
    direction: str,
) -> tuple[list[str], list[str], str]:
    if not folder_path:
        raise gr.Error("先に画像フォルダーを選択してください。")
    folder = Path(folder_path).expanduser()
    if not folder.is_dir():
        raise gr.Error("選択したフォルダーが見つかりません。")
    try:
        images = [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES
        ]
        gallery = []
        paths = []
        unreadable = 0
        for path in _sort_folder_images(images, sort_by, direction):
            try:
                gallery.append(_thumbnail_path(path))
                paths.append(str(path))
            except ImageInputError:
                unreadable += 1
    except OSError as error:
        raise gr.Error(f"フォルダーを読み込めませんでした：{error}") from error

    sort_label = FOLDER_SORT_LABELS[sort_by]
    direction_label = SORT_DIRECTION_LABELS[direction]
    status = (
        f"**{len(paths)}枚** / **{sort_label}・{direction_label}** / "
        f"`{folder}`"
        if paths
        else f"対応画像が見つかりませんでした。`{folder}`"
    )
    if unreadable:
        status += f" 読み込めない画像{unreadable}件は除外しました。"
    return gallery, paths, status


def choose_folder(
    sort_by: str,
    direction: str,
) -> tuple[str, list[str], list[str], str, None, None]:
    if sys.platform != "darwin":
        raise gr.Error("Finderでのフォルダー選択はmacOSで利用できます。")
    result = subprocess.run(
        [
            "osascript",
            "-e",
            'POSIX path of (choose folder with prompt "画像フォルダーを選択")',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        if "-128" in result.stderr:
            raise gr.Error("フォルダー選択をキャンセルしました。")
        raise gr.Error(f"Finderを開けませんでした：{result.stderr.strip()}")

    folder_path = result.stdout.strip()
    gallery, paths, status = load_folder(folder_path, sort_by, direction)
    return folder_path, gallery, paths, status, None, None


def refresh_folder(
    folder_path: str | None,
    sort_by: str,
    direction: str,
    selected_folder_image: str | None,
    displayed_image: str | None,
) -> tuple[list[str], list[str], str, str | None, str | None]:
    gallery, paths, status = load_folder(folder_path, sort_by, direction)
    if selected_folder_image and Path(selected_folder_image).is_file():
        preview = _thumbnail_path(Path(selected_folder_image))
        return gallery, paths, status, preview, selected_folder_image
    if selected_folder_image:
        return gallery, paths, status, None, None
    displayed = (
        displayed_image
        if displayed_image and Path(displayed_image).is_file()
        else None
    )
    return gallery, paths, status, displayed, None


def select_folder_image(
    paths: list[str],
    evt: gr.SelectData,
) -> tuple[str, str, str]:
    if not isinstance(evt.index, int) or not 0 <= evt.index < len(paths):
        raise gr.Error("画像を選択できませんでした。")
    selected = paths[evt.index]
    if not Path(selected).is_file():
        raise gr.Error("選択した画像が見つかりません。")
    return (
        _thumbnail_path(Path(selected)),
        selected,
        f"**選択中**：`{Path(selected).name}`",
    )


def run_analysis(
    image_path: str | None,
    selected_folder_image: str | None,
    general_threshold: float,
    character_threshold: float,
    environment_preset: str,
) -> tuple[str, str, str, str, str]:
    source_path = selected_folder_image or image_path
    if not source_path:
        raise gr.Error("画像を選択してください。")

    result = analyze(
        Path(source_path),
        general_threshold=general_threshold,
        character_threshold=character_threshold,
        include_natural_language=False,
        environment_preset=environment_preset,
    )
    danbooru = result["danbooru"]
    faithful_prompt = result["faithful_prompt"]
    rating = danbooru["rating"]
    status = (
        f"完了：{result['total_seconds']:.2f}秒 / "
        f"rating: {rating['tag']} ({rating['score']:.3f})"
    )
    return (
        faithful_prompt["prompt"],
        token_status(faithful_prompt["prompt"]),
        danbooru["prompt"],
        token_status(danbooru["prompt"]),
        status,
    )


def build_app() -> gr.Blocks:
    saved_settings = load_settings()
    with gr.Blocks(title="image2prompt") as app:
        gr.Markdown(
            "# image2prompt\n"
            "画像から忠実度優先形式とDanbooruタグ形式の"
            "プロンプトを生成します。"
        )
        folder_path = gr.State("")
        folder_paths = gr.State([])
        selected_folder_image = gr.State(None)
        with gr.Accordion("解析設定", open=False):
            gr.Markdown(
                "タグを採用する範囲と、解析結果へ追加する任意の環境演出を"
                "設定します。"
            )
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("#### タグ検出")
                    with gr.Row():
                        general_threshold = gr.Slider(
                            0,
                            1,
                            value=saved_settings["general_threshold"],
                            step=0.01,
                            label="一般タグしきい値",
                            info="低くするほど多くの要素を採用します。",
                        )
                        character_threshold = gr.Slider(
                            0,
                            1,
                            value=saved_settings["character_threshold"],
                            step=0.01,
                            label="キャラクタータグしきい値",
                            info="固有キャラクター名の採用基準です。",
                        )
                with gr.Column(scale=1, min_width=320):
                    gr.Markdown("#### 環境プリセット")
                    environment_preset = gr.Dropdown(
                        choices=ENVIRONMENT_PRESET_CHOICES,
                        value=saved_settings["environment_preset"],
                        label="追加する演出",
                        info="適用なしでは解析結果だけを使用します。",
                    )
            with gr.Row():
                with gr.Column(scale=3):
                    settings_status = gr.Markdown(
                        "変更後に保存すると、次回起動時に復元されます。"
                    )
                with gr.Column(scale=1, min_width=220):
                    save_settings_button = gr.Button(
                        "解析設定を保存",
                        size="sm",
                    )

        with gr.Accordion("フォルダーから画像を選択", open=False):
            with gr.Row():
                choose_folder_button = gr.Button(
                    "Finderで画像フォルダーを選択",
                    variant="secondary",
                    scale=3,
                )
                reload_folder_button = gr.Button("再読み込み", scale=1)
            with gr.Row():
                folder_sort = gr.Dropdown(
                    choices=FOLDER_SORT_CHOICES,
                    value="name",
                    label="並び順",
                    scale=2,
                )
                sort_direction = gr.Radio(
                    choices=SORT_DIRECTION_CHOICES,
                    value="ascending",
                    label="方向",
                    scale=1,
                )
            folder_status = gr.Markdown(
                "Finderから画像フォルダーを選択してください。"
            )
            gallery = gr.Gallery(
                label="画像一覧（クリックして選択）",
                columns=5,
                rows=3,
                height=480,
                object_fit="contain",
                allow_preview=False,
                show_download_button=False,
                show_fullscreen_button=False,
            )

        with gr.Row():
            with gr.Column(scale=3):
                image = gr.Image(
                    label="選択画像（単体アップロードも可能）",
                    type="filepath",
                    sources=["upload"],
                    height=520,
                )
            with gr.Column(scale=2):
                run_button = gr.Button("解析する", variant="primary")
                status = gr.Markdown()
                faithful_output = gr.Textbox(
                    label="忠実度優先形式（推奨・ComfyUI向け）",
                    info="信頼度0.50以上のWDタグを整理し、推測を加えず文章化します。",
                    lines=8,
                    show_copy_button=True,
                )
                faithful_tokens = gr.Markdown(token_status(""))
                danbooru_output = gr.Textbox(
                    label="Danbooruタグ形式",
                    lines=6,
                    show_copy_button=True,
                )
                danbooru_tokens = gr.Markdown(token_status(""))
        run_button.click(
            fn=run_analysis,
            inputs=[
                image,
                selected_folder_image,
                general_threshold,
                character_threshold,
                environment_preset,
            ],
            outputs=[
                faithful_output,
                faithful_tokens,
                danbooru_output,
                danbooru_tokens,
                status,
            ],
        )
        save_settings_button.click(
            fn=save_settings,
            inputs=[
                general_threshold,
                character_threshold,
                environment_preset,
            ],
            outputs=settings_status,
            show_progress="hidden",
        )
        choose_folder_button.click(
            fn=choose_folder,
            inputs=[folder_sort, sort_direction],
            outputs=[
                folder_path,
                gallery,
                folder_paths,
                folder_status,
                image,
                selected_folder_image,
            ],
        )
        for component in (folder_sort, sort_direction):
            component.change(
                fn=refresh_folder,
                inputs=[
                    folder_path,
                    folder_sort,
                    sort_direction,
                    selected_folder_image,
                    image,
                ],
                outputs=[
                    gallery,
                    folder_paths,
                    folder_status,
                    image,
                    selected_folder_image,
                ],
                show_progress="hidden",
            )
        reload_folder_button.click(
            fn=refresh_folder,
            inputs=[
                folder_path,
                folder_sort,
                sort_direction,
                selected_folder_image,
                image,
            ],
            outputs=[
                gallery,
                folder_paths,
                folder_status,
                image,
                selected_folder_image,
            ],
        )
        gallery.select(
            fn=select_folder_image,
            inputs=folder_paths,
            outputs=[image, selected_folder_image, folder_status],
        )
        image.upload(
            fn=lambda: None,
            outputs=selected_folder_image,
            show_progress="hidden",
        )
        image.clear(
            fn=lambda: None,
            outputs=selected_folder_image,
            show_progress="hidden",
        )
    return app


def main() -> None:
    build_app().queue(default_concurrency_limit=1).launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=False,
    )


if __name__ == "__main__":
    main()
