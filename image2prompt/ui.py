"""Local Gradio UI for image2prompt."""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from .analyze import analyze

IMAGE_SUFFIXES = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
)
SETTINGS_PATH = (
    Path.home() / "Library" / "Application Support" / "image2prompt" / "settings.json"
)
DEFAULT_SETTINGS: dict[str, float | int] = {
    "general_threshold": 0.35,
    "character_threshold": 0.85,
    "max_new_tokens": 128,
}


def _validated_settings(
    general_threshold: object,
    character_threshold: object,
    max_new_tokens: object,
) -> dict[str, float | int]:
    general = float(general_threshold)
    character = float(character_threshold)
    tokens = int(max_new_tokens)
    if not 0 <= general <= 1 or not 0 <= character <= 1 or not 32 <= tokens <= 500:
        raise ValueError("設定値が許容範囲外です。")
    return {
        "general_threshold": general,
        "character_threshold": character,
        "max_new_tokens": tokens,
    }


def load_settings(path: Path = SETTINGS_PATH) -> dict[str, float | int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _validated_settings(
            data["general_threshold"],
            data["character_threshold"],
            data["max_new_tokens"],
        )
    except (KeyError, OSError, TypeError, ValueError):
        return DEFAULT_SETTINGS.copy()


def save_settings(
    general_threshold: float,
    character_threshold: float,
    max_new_tokens: float,
    path: Path = SETTINGS_PATH,
) -> str:
    try:
        settings = _validated_settings(
            general_threshold,
            character_threshold,
            max_new_tokens,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except (OSError, ValueError) as error:
        raise gr.Error(f"解析設定を保存できませんでした：{error}") from error
    return "解析設定を保存しました。"


def load_folder(files: list[str] | None) -> tuple[list[str], list[str], str]:
    uploaded = [Path(path) for path in files or [] if Path(path).is_file()]
    paths = sorted(
        (str(path) for path in uploaded if path.suffix.casefold() in IMAGE_SUFFIXES),
        key=lambda path: Path(path).name.casefold(),
    )
    ignored = len(uploaded) - len(paths)
    status = (
        f"**{len(paths)}枚**の画像を読み込みました。解析する画像を選択してください。"
        if paths
        else "対応画像が見つかりませんでした。"
    )
    if ignored:
        status += f" 画像以外の{ignored}件は除外しました。"
    return paths, paths, status


def select_folder_image(paths: list[str], evt: gr.SelectData) -> tuple[str, str]:
    if not isinstance(evt.index, int) or not 0 <= evt.index < len(paths):
        raise gr.Error("画像を選択できませんでした。")
    selected = paths[evt.index]
    if not Path(selected).is_file():
        raise gr.Error("選択した画像が見つかりません。")
    return selected, f"**選択中**：`{Path(selected).name}`"


def run_analysis(
    image_path: str | None,
    general_threshold: float,
    character_threshold: float,
    max_new_tokens: float,
) -> tuple[str, str, str, str]:
    if not image_path:
        raise gr.Error("画像を選択してください。")

    result = analyze(
        Path(image_path),
        general_threshold=general_threshold,
        character_threshold=character_threshold,
        max_new_tokens=int(max_new_tokens),
    )
    danbooru = result["danbooru"]
    faithful_prompt = result["faithful_prompt"]
    natural_language = result["natural_language"]
    rating = danbooru["rating"]
    status = (
        f"完了：{result['total_seconds']:.2f}秒 / "
        f"rating: {rating['tag']} ({rating['score']:.3f})"
    )
    return (
        faithful_prompt["prompt"],
        danbooru["prompt"],
        natural_language["prompt"],
        status,
    )


def build_app() -> gr.Blocks:
    saved_settings = load_settings()
    with gr.Blocks(title="image2prompt") as app:
        gr.Markdown(
            "# image2prompt\n"
            "画像から忠実度優先形式、Danbooruタグ形式、"
            "SmolVLM自然言語形式のプロンプトを生成します。"
        )
        folder_paths = gr.State([])
        with gr.Accordion("解析設定", open=False), gr.Row():
            general_threshold = gr.Slider(
                0,
                1,
                value=saved_settings["general_threshold"],
                step=0.01,
                label="一般タグしきい値",
            )
            character_threshold = gr.Slider(
                0,
                1,
                value=saved_settings["character_threshold"],
                step=0.01,
                label="キャラクタータグしきい値",
            )
            max_new_tokens = gr.Slider(
                32,
                500,
                value=saved_settings["max_new_tokens"],
                step=1,
                label="自然言語の最大トークン数",
            )
            with gr.Column(min_width=220):
                save_settings_button = gr.Button("解析設定を保存", size="sm")
                settings_status = gr.Markdown(
                    "変更後に保存すると、次回起動時に復元されます。"
                )

        with gr.Accordion("フォルダーから画像を選択", open=False):
            folder_files = gr.UploadButton(
                "Finderで画像フォルダーを選択",
                file_count="directory",
                type="filepath",
            )
            folder_status = gr.Markdown(
                "フォルダーはこのボタンから選択してください。"
                "フォルダーのドラッグ＆ドロップには対応していません。"
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
                danbooru_output = gr.Textbox(
                    label="Danbooruタグ形式",
                    lines=6,
                    show_copy_button=True,
                )
                natural_output = gr.Textbox(
                    label="SmolVLM自然言語形式（参考）",
                    lines=6,
                    show_copy_button=True,
                )

        run_button.click(
            fn=run_analysis,
            inputs=[
                image,
                general_threshold,
                character_threshold,
                max_new_tokens,
            ],
            outputs=[
                faithful_output,
                danbooru_output,
                natural_output,
                status,
            ],
        )
        save_settings_button.click(
            fn=save_settings,
            inputs=[
                general_threshold,
                character_threshold,
                max_new_tokens,
            ],
            outputs=settings_status,
            show_progress="hidden",
        )
        folder_files.upload(
            fn=load_folder,
            inputs=folder_files,
            outputs=[gallery, folder_paths, folder_status],
        )
        gallery.select(
            fn=select_folder_image,
            inputs=folder_paths,
            outputs=[image, folder_status],
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
