$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$modelDir = "models/wd-swinv2-tagger-v3"
$iconPath = "packaging/assets/image2prompt.ico"
foreach ($file in @("model.onnx", "selected_tags.csv")) {
    $path = Join-Path $modelDir $file
    if (-not (Test-Path $path -PathType Leaf)) {
        throw "Missing $path"
    }
}
if (-not (Test-Path $iconPath -PathType Leaf)) {
    throw "Missing $iconPath"
}

$env:PYINSTALLER_CONFIG_DIR = ".cache/pyinstaller-windows"
$env:UV_CACHE_DIR = ".cache/uv"
$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onedir",
    "--windowed",
    "--name", "image2prompt",
    "--icon", $iconPath,
    "--paths", ".",
    "--additional-hooks-dir", "packaging/hooks",
    "--exclude-module", "transformers",
    "--exclude-module", "tokenizers",
    "--exclude-module", "image2prompt.smolvlm_caption",
    "--exclude-module", "image2prompt.florence2_caption",
    "--collect-data", "gradio_client",
    "--collect-data", "safehttpx",
    "--collect-data", "groovy",
    "--add-data", "${modelDir}:${modelDir}",
    "packaging/desktop_entry.py"
)

uv run --with pyinstaller==6.21.0 --with pywebview==6.2.1 pyinstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Built dist/image2prompt/image2prompt.exe"
