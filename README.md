# image2prompt

画像を解析し、画像生成向けの次の2種類のプロンプトを生成するローカルアプリです。

- Danbooruタグ形式
- 自然言語形式

## 現在の状態

標準画像の読み込みとモデル入力用前処理を実装しています。次にWD Tagger系モデルによるタグ抽出を検証します。

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

## 次のマイルストーン

1. JPEG、PNG、WebP、BMP、TIFF、GIFの読み込み確認
2. EXIF回転、RGB変換、縦横比を維持した画像前処理
3. WD Tagger候補のローカル推論
4. 代表画像での精度・速度測定
5. 自然言語モデル候補の比較

詳細は[作業計画](./image2prompt%20作業計画.txt)を参照してください。

## 進捗記録

- 作業が進んだ段階で[WORK_LOG.md](./WORK_LOG.md)へ追記します。
- 作業を中断する際は[NEXT_RESUME_POINT.md](./NEXT_RESUME_POINT.md)を更新します。

## ライセンス

未決定です。公開前にライセンスを選定します。
