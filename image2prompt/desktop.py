"""Run the local Gradio UI inside a native application window."""

from __future__ import annotations

from .runtime import shutdown_runtime
from .ui import build_app


def main() -> None:
    import webview

    app = build_app().queue(default_concurrency_limit=1)
    _, local_url, _ = app.launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=False,
        prevent_thread_lock=True,
        quiet=True,
        show_api=False,
    )
    try:
        window = webview.create_window(
            "image2prompt",
            local_url,
            width=1280,
            height=900,
            min_size=(800, 600),
        )
        window.events.closing += shutdown_runtime
        webview.start()
    finally:
        try:
            shutdown_runtime()
        finally:
            app.close(verbose=False)


if __name__ == "__main__":
    main()
