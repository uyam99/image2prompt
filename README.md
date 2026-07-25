# image2prompt

画像を解析し、画像生成向けの次の3種類のプロンプトを生成するローカルアプリです。

- 忠実度優先形式（推奨・ComfyUI向け）
- Danbooruタグ形式
- SmolVLM自然言語形式（参考）

## 現在の状態

基本版：`v0.1.0`

標準画像の前処理、WD SwinV2 Tagger v3によるDanbooruタグ抽出、
タグを決定的に文章化する忠実度優先形式、SmolVLM-256Mによる自然言語
プロンプト生成、単一画像Web UIを実装しています。

GitHubリポジトリ（Private）：[uyam99/image2prompt](https://github.com/uyam99/image2prompt)

## 対象環境

- Apple Silicon Mac
- Intel Mac

Windows対応とスタンドアロンアプリ化は、Mac版MVPの完成後に検討します。

## 開発方針

- image2prompt独自のアプリとして実装します。
- Dataset Tag Editorなどの既存ソフトウェアは、実装方法を調査する参考資料としてのみ扱います。
- 未検証のモデルや依存パッケージは、比較検証後に固定します。
- モデルファイル、生成結果、ローカル設定はGitへ登録しません。

## 画像前処理の確認

Python 3.12と[uv](https://docs.astral.sh/uv/)を使用します。

```sh
uv sync
uv run python -m unittest
uv run image2prompt-check /path/to/image.jpg
```

最後のコマンドは、解析用に正方形化したプレビューを`outputs/`へ保存し、元画像の形式・寸法と処理後の情報を表示します。元画像は変更しません。

## Danbooruタグ抽出

モデルはGitへ登録しないため、初回だけ次のコマンドで取得します（約467 MB）。

```sh
uvx --from huggingface_hub hf download \
  SmilingWolf/wd-swinv2-tagger-v3 \
  model.onnx selected_tags.csv \
  --revision 627aef95638667ddcaa3ac8ae625e88ea5b02f51 \
  --local-dir models/wd-swinv2-tagger-v3
```

タグと信頼度をJSONで表示します。

```sh
uv run image2prompt-tag /path/to/image.jpg
```

複数画像を指定すると、モデルを1回だけ読み込んで順番に処理します。

```sh
uv run image2prompt-tag /path/to/first.jpg /path/to/second.png
```

初期しきい値は一般タグ0.35、キャラクタータグ0.85です。必要なら
`--general-threshold`と`--character-threshold`で変更できます。ratingは情報として
表示しますが、現在は画像やタグの除外には使用しません。

使用モデル：[SmilingWolf/wd-swinv2-tagger-v3](https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3)
（Apache-2.0）

## 忠実度優先プロンプト（推奨）

WD Taggerで信頼度0.50以上となったタグを、競合・重複を除去してから定型文へ
変換します。言語モデルによる推測を挟まないため、元画像にない物体や状態の
追加を抑えたい場合に使用します。

```sh
uv run image2prompt-faithful /path/to/image.jpg
```

出力される`prompt`をComfyUIなどの画像生成環境へコピーして使用できます。
比較実験用に`--faithful-threshold`でしきい値を変更できますが、現在の推奨値は
3枚の固定画像で確認した0.50です。

## SmolVLM自然言語プロンプト生成（参考）

PyTorchを使わず、既存のONNX Runtimeで動くSmolVLM-256Mの公式ONNX版を使用します。
初回だけ次のファイルを取得します（合計約540 MB）。

```sh
uvx --from huggingface_hub hf download \
  HuggingFaceTB/SmolVLM-256M-Instruct \
  config.json generation_config.json preprocessor_config.json \
  processor_config.json chat_template.json tokenizer.json \
  tokenizer_config.json special_tokens_map.json added_tokens.json \
  merges.txt vocab.json \
  onnx/vision_encoder.onnx \
  onnx/embed_tokens_int8.onnx \
  onnx/decoder_model_merged_int8.onnx \
  --revision 7e3e67edbbed1bf9888184d9df282b700a323964 \
  --local-dir models/smolvlm-256m-instruct
```

自然言語プロンプトをJSONで表示します。

```sh
uv run image2prompt-caption /path/to/image.jpg
```

被写体だけでなく、外見、衣装、姿勢、動作、背景、天候、照明、構図、色、
画風を含む詳細な説明を生成します。生成上限は初期値128トークンで、
`--max-new-tokens`により最大500トークンまで変更できます。

```sh
uv run image2prompt-caption /path/to/image.jpg --max-new-tokens 500
```

Intel Macでは512px入力、CPU実行を初期基準としています。使用モデル：
[HuggingFaceTB/SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)
（Apache-2.0）

## 3種類のプロンプトを同時生成

単一画像から忠実度優先形式、Danbooruタグ形式、SmolVLM自然言語形式を
同じJSONへ出力します。

```sh
uv run image2prompt-analyze /path/to/image.jpg
```

タグしきい値と自然言語の生成上限も指定できます。

```sh
uv run image2prompt-analyze \
  --general-threshold 0.35 \
  --character-threshold 0.85 \
  --max-new-tokens 500 \
  /path/to/image.jpg
```

## ローカルWeb UI

```sh
uv run image2prompt-web
```

表示された`http://127.0.0.1:7860`をブラウザーで開き、画像を選択して
「解析する」を押します。一般タグとキャラクタータグのしきい値、自然言語の
最大トークン数は、上部の「解析設定」を開くと変更できます。3種類の結果は
個別にコピーできます。選択画像の右側では、ComfyUI向けの忠実度優先形式を
先頭に表示し、その下に比較用のDanbooruタグ形式とSmolVLM自然言語形式を
表示します。外部公開や画像の送信は行いません。

解析設定の3項目は「解析設定を保存」を押すと保存され、次回起動時に復元されます。
Mac版の保存先は
`~/Library/Application Support/image2prompt/settings.json`です。
設定ファイルが存在しない場合や内容が壊れている場合は既定値を使用します。

「フォルダーから画像を選択」を開き、「Finderで画像フォルダーを選択」ボタン
からフォルダーを指定すると、画像が縦横比を保ったサムネイルで並びます。
ファイル名は一覧へ重ねず、選択中の画像名だけを一覧の上へ表示します。
フォルダーのドラッグ＆ドロップには対応していません。サムネイルを1枚選択
してから「解析する」を押すと、その画像だけを解析します。`.DS_Store`など
画像以外のファイルは自動的に除外します。
フォルダー内の全画像を一括解析する機能はまだ実装していません。

## 次のマイルストーン

1. JPEG、PNG、WebP、BMP、TIFF、GIFの読み込み確認：完了
2. EXIF回転、RGB変換、縦横比を維持した画像前処理：完了
3. WD Tagger候補のローカル推論：完了
4. 単一画像Web UI：完了
5. 自然言語モデル候補の比較：SmolVLM-256MをMVPへ採用
6. フォルダー内の画像一覧と単一選択：完了
7. 忠実度優先プロンプト生成：完了
8. 複数画像の一括処理、進捗表示、CSV出力：保留

詳細は[作業計画](./image2prompt%20作業計画.txt)を参照してください。

## 進捗記録

- 作業が進んだ段階で[WORK_LOG.md](./WORK_LOG.md)へ追記します。
- 作業を中断する際は[NEXT_RESUME_POINT.md](./NEXT_RESUME_POINT.md)を更新します。

## ライセンス

未決定です。公開前にライセンスを選定します。
