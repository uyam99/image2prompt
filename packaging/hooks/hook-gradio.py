from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, get_package_paths

_, package_dir = get_package_paths("gradio")
package_dir = Path(package_dir)
datas = collect_data_files("gradio")
for pattern in ("*.py", "*.pyi"):
    datas.extend(
        (
            str(source),
            str(Path("gradio") / source.relative_to(package_dir).parent),
        )
        for source in package_dir.rglob(pattern)
    )
