#!/bin/zsh
set -euo pipefail

cd "${0:A:h}/.."

model_dir="models/wd-swinv2-tagger-v3"
icon_path="packaging/assets/image2prompt.icns"
uv_path="${IMAGE2PROMPT_UV:-$(command -v uv)}"
for file in model.onnx selected_tags.csv; do
    [[ -f "$model_dir/$file" ]] || {
        print -u2 "Missing $model_dir/$file"
        exit 1
    }
done
[[ -f "$icon_path" ]] || {
    print -u2 "Missing $icon_path"
    exit 1
}
[[ -f "${uv_path:A}" ]] || {
    print -u2 "Missing uv executable"
    exit 1
}

PYINSTALLER_CONFIG_DIR=.cache/pyinstaller \
UV_CACHE_DIR=.cache/uv uv run \
    --with pyinstaller==6.21.0 \
    --with pywebview==6.2.1 \
    pyinstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name image2prompt \
    --icon "$icon_path" \
    --paths . \
    --additional-hooks-dir packaging/hooks \
    --osx-bundle-identifier com.uyam99.image2prompt \
    --exclude-module transformers \
    --exclude-module tokenizers \
    --exclude-module image2prompt.smolvlm_caption \
    --exclude-module image2prompt.florence2_caption \
    --collect-data gradio_client \
    --collect-data safehttpx \
    --collect-data groovy \
    --add-data "$model_dir:$model_dir" \
    --add-data "image2prompt/florence_runner.py:image2prompt" \
    --add-binary "${uv_path:A}:bin" \
    packaging/desktop_entry.py

print "Built dist/image2prompt.app"
