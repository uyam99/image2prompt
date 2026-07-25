"""Local Gradio UI for image2prompt."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from .analyze import analyze

IMAGE_SUFFIXES = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
)


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
) -> tuple[str, str, str]:
    if not image_path:
        raise gr.Error("画像を選択してください。")

    result = analyze(
        Path(image_path),
        general_threshold=general_threshold,
        character_threshold=character_threshold,
        max_new_tokens=int(max_new_tokens),
    )
    danbooru = result["danbooru"]
    natural_language = result["natural_language"]
    rating = danbooru["rating"]
    status = (
        f"完了：{result['total_seconds']:.2f}秒 / "
        f"rating: {rating['tag']} ({rating['score']:.3f})"
    )
    return danbooru["prompt"], natural_language["prompt"], status


def build_app() -> gr.Blocks:
    with gr.Blocks(title="image2prompt") as app:
        gr.Markdown(
            "# image2prompt\n"
            "画像からDanbooruタグ形式と自然言語形式のプロンプトを生成します。"
        )
        folder_paths = gr.State([])
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
                general_threshold = gr.Slider(
                    0,
                    1,
                    value=0.35,
                    step=0.01,
                    label="一般タグしきい値",
                )
                character_threshold = gr.Slider(
                    0,
                    1,
                    value=0.85,
                    step=0.01,
                    label="キャラクタータグしきい値",
                )
                max_new_tokens = gr.Slider(
                    32,
                    500,
                    value=128,
                    step=1,
                    label="自然言語の最大トークン数",
                )
                run_button = gr.Button("解析する", variant="primary")
                status = gr.Markdown()

        danbooru_output = gr.Textbox(
            label="Danbooruタグ形式",
            lines=8,
            show_copy_button=True,
        )
        natural_output = gr.Textbox(
            label="自然言語形式",
            lines=10,
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
            outputs=[danbooru_output, natural_output, status],
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
