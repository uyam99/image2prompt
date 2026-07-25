# image2prompt 作業履歴

## 2026-07-21：計画策定とリポジトリ準備

### 実施内容

- 当初の作業計画を確認し、実装方針を整理した。
- image2promptを既存アプリの派生ではなく、独立したアプリとして開発する方針を確定した。
- Dataset Tag Editorは、画像前処理、WD Tagger、ONNX Runtime、しきい値処理などを調査する参考資料としてのみ扱うことを確認した。
- Danbooruタグ形式と自然言語形式の2種類を生成対象とした。
- 初期版をPythonとGradioによるローカルWebアプリ候補とした。
- Apple Silicon MacとIntel Macを初期対象とした。
- JPEG、PNG、WebP、BMP、TIFF、GIFを初期対応候補とした。
- アニメーション形式と複数ページTIFFは、初期版では先頭フレームのみを扱う方針とした。
- 成人向けコンテンツ専用の判定やON／OFF切り替えは、基本機能完成後まで延期した。
- Danbooruタグ生成の初期候補をWD Tagger系モデルとONNX Runtimeの組み合わせとした。
- 自然言語モデルは、ローカルモデルの品質・速度比較後に決定することとした。
- 作業計画書、README、Git除外設定を作成した。
- `main`ブランチでGitリポジトリを初期化し、初期コミット`b236990`を作成した。
- 実作業ルートを次のサブフォルダーへ移した。

  `/Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt`

### 現在の成果物

- `README.md`
- `image2prompt 作業計画.txt`
- `.gitignore`
- `WORK_LOG.md`
- `NEXT_RESUME_POINT.md`

### 未実施

- アプリケーションコードの作成
- Python依存関係とバージョンの固定
- モデルのダウンロードと推論検証
- テスト用画像の準備
- Gitリモートの登録とpush
- 公開ライセンスの選定
- Git作成者名・メールアドレスの確認

### 記録運用

- 機能、検証結果、重要な判断が増えた段階で、このファイルへ日付付きで追記する。
- 中断時は`NEXT_RESUME_POINT.md`を、次に着手する具体的な作業が分かる状態へ更新する。

## 2026-07-25：標準画像の読み込みと前処理

### 実施内容

- Intel MacとApple Silicon Macの共通基準をPython 3.12とした。
- `uv`による仮想環境とロックファイルを追加した。
- Pillow 12.3.0を使用した画像前処理を実装した。
- ファイル内容からJPEG、PNG、WebP、BMP、TIFF、GIFを判定するようにした。
- EXIF回転、先頭フレーム選択、透過画像の白背景合成、RGB変換を実装した。
- 縦横比を維持し、白い余白で指定サイズの正方形へ変換するようにした。
- 100 MiBのファイル上限と4,000万画素の初期上限を設定した。
- 破損画像、未対応形式、上限超過を`ImageInputError`として扱うようにした。
- `image2prompt-check`コマンドで処理結果をJSON表示し、確認用PNGを保存できるようにした。
- 標準`unittest`による5件の自動チェックを追加した。

### 検証結果

- 6種類の標準画像形式：成功
- EXIF回転：成功
- 透過画像の白背景合成：成功
- アニメーションGIFの先頭フレーム選択：成功
- 破損画像と画素上限の拒否：成功
- 640×360の透過PNGから448×448 RGBプレビューの生成：成功

実行コマンド：

```sh
uv sync
uv run python -m unittest
uv run image2prompt-check /path/to/image.jpg
```

### 互換性判断

- Pillow 12系はPython 3.10から3.14をサポートしている。
- 最新ONNX RuntimeはmacOS Intel向けバイナリを終了している。
- 次の検証では、Intel／Apple両対応のUniversal2 wheelがあるONNX Runtime 1.20.1を候補とする。
- ONNX Runtimeは画像前処理に不要なため、今回は依存関係へ追加していない。

### 次の作業

- ONNX Runtime 1.20.1のIntel Mac上での導入確認
- WD Tagger候補モデルと`selected_tags.csv`の取得
- 1枚の画像からDanbooruタグと信頼度を出力する最小推論
