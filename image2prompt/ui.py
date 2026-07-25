"""Local Gradio UI for image2prompt."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from .analyze import analyze


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
        with gr.Row():
            image = gr.Image(
                label="入力画像",
                type="filepath",
                sources=["upload"],
                height=520,
            )
            with gr.Column():
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
    return app


def main() -> None:
    build_app().queue(default_concurrency_limit=1).launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=False,
    )


if __name__ == "__main__":
    main()
