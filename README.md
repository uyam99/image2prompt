# image2prompt

画像を解析し、画像生成向けの次の2種類のプロンプトを生成するローカルアプリです。

- Danbooruタグ形式
- 自然言語形式

## 現在の状態

標準画像の前処理と、WD SwinV2 Tagger v3によるDanbooruタグ抽出を実装しています。

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

## 次のマイルストーン

1. JPEG、PNG、WebP、BMP、TIFF、GIFの読み込み確認：完了
2. EXIF回転、RGB変換、縦横比を維持した画像前処理：完了
3. WD Tagger候補のローカル推論：完了
4. 複数の代表画像での精度・速度測定
5. 自然言語モデル候補の比較

詳細は[作業計画](./image2prompt%20作業計画.txt)を参照してください。

## 進捗記録

- 作業が進んだ段階で[WORK_LOG.md](./WORK_LOG.md)へ追記します。
- 作業を中断する際は[NEXT_RESUME_POINT.md](./NEXT_RESUME_POINT.md)を更新します。

## ライセンス

未決定です。公開前にライセンスを選定します。
