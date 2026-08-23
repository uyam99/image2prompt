# 次回の再開ポイント

更新日：2026-08-23

## 作業ルート

`/Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt`

以後の編集、Git操作、テスト実行はこのフォルダーを基準にする。

## 次回最初の作業

GitHub Actionsの成果物ストレージ使用量が再計算された後、Apple Silicon／Windowsの
失敗runを再実行し、実機テスト用Artifactを取得する。旧Artifactは削除済みで、
GitHubの案内上、容量反映には削除から6〜12時間かかる。

対象run（commit `4ae1e34`）：

- Apple Silicon：`32625753202`
- Windows：`32625753217`

成果物：

- `image2prompt-macos-arm64`
- `image2prompt-windows-x64`

両runはattempt 2まで、テスト、アプリ生成、バンドル検証に成功し、最後のArtifact
アップロードだけ容量上限で失敗している。Artifactsの保存期間は14日。生成後は
ユーザーが各実機で以下を確認する。

## Apple Silicon実機テスト

1. ZIPを展開し、`image2prompt.app`をFinderから起動する。
2. 「忠実度優先」「自然言語（Florence）」の2タブが表示されることを確認する。
3. 単体アップロードとフォルダー選択から忠実度優先解析を実行する。
4. 「自然言語を生成」を初めて押し、推論環境と約3.4GBのモデル取得が完了することを確認する。
5. 2回目以降は取得済み環境を再利用することを確認する。
6. 最終プロンプト、Florence本文、画風、空のWD補足、撮影設定が表示されることを確認する。
7. 詳細編集とWD補足の追加・解除が最終プロンプトへ反映されることを確認する。
8. アプリ終了後にプロセスとTCP 7860／7861が残らないことを確認する。

## Windows実機テスト

1. Artifactをフォルダーごと展開する。`image2prompt.exe`だけを取り出さない。
2. `image2prompt.exe`を起動し、専用ウィンドウと2つの出力タブを確認する。
3. 単体アップロード、フォルダー選択、忠実度優先解析を確認する。
4. 自然言語の初回ダウンロードと2回目以降の再利用を確認する。
5. Florence本文、画風、空のWD補足、撮影設定、最終プロンプトを確認する。
6. 詳細編集とWD補足の追加・解除を確認する。
7. 終了後に`image2prompt.exe`と子プロセス、TCP 7860／7861が残らないことを確認する。

Windows 10で専用ウィンドウが開かない場合は、Microsoft Edge WebView2 Runtimeの
有無を先に確認する。

## 現在完了している作業

- 忠実度優先形式は安定版`v0.2.0`の既定・推奨出力として維持した。
- Florence自然言語形式を任意機能として採用した。
- 画像入力と解析設定を共有し、結果を忠実度優先／自然言語タブへ整理した。
- 自然言語タブは最終プロンプトを先に表示し、編集欄を「詳細編集」へまとめた。
- `image2prompt/florence_runner.py`を製品用の隔離実行スクリプトとして追加した。
- Windowsでバンドルされた`bin/uv.exe`を検出できるようにした。
- macOS／WindowsビルドへFlorenceランナーと各OS用`uv`を追加した。
- CIの成果物検証へランナーと`uv`の存在確認を追加した。
- Intel x86_64版`dist/image2prompt.app`を再ビルドし、実起動と自然言語生成を確認した。

Intel版は約854MB、アプリ本体と同梱`uv`はx86_64、adhoc署名検証済み。
FlorenceモデルとPyTorchは同梱していない。バンドル内ランナーから実画像を
29.55秒で処理し、終了後にプロセスとTCP 7860／7861が残らないことを確認した。

## 継続検証コマンド

```sh
cd /Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt
UV_CACHE_DIR=.cache/uv uv run python -m unittest
UV_CACHE_DIR=.cache/uv uv run ruff check .
git diff --check
git status --short --branch
```

Intel版の再ビルド：

```sh
zsh packaging/build_macos.sh
codesign --verify --deep --strict dist/image2prompt.app
```

## 配布境界

- Florenceモデル約3.4GBとPyTorchはアプリへ同梱しない。
- 初回の自然言語生成時だけネットワーク接続を必要とする。
- Macの保存先は`~/Library/Application Support/image2prompt/`、Windowsは
  `%APPDATA%\image2prompt\`である。
- WD補足は自動追加せず、初期状態を空にする。
- 忠実度優先形式を自然言語形式で置き換えない。
- ONNX変換、MPS最適化、複数画像一括処理、インストーラー、自動更新は保留する。
- 不採用比較用の`experiments/`は削除せずローカルに保全するが、製品ランタイムは参照しない。

## Git状態

`main`と`origin/main`は`4ae1e34`で一致している。自然言語UI、製品ランナー、
macOS／Windowsビルド、workflow、テスト、文書はcommit・push済みである。
`image2prompt/wd_tagger.py`、`tests/test_wd_tagger.py`、`experiments/`には比較研究用の
未コミット差分があり、そのまま保全している。モデル、キャッシュ、生成結果、`dist/`は
Git追跡対象外である。
