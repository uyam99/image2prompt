# 次回の再開ポイント

更新日：2026-07-21

## 作業ルート

`/Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt`

以後の編集、Git操作、テスト実行はこのフォルダーを基準にする。

## 再開時に最初に確認するもの

1. `README.md`
2. `image2prompt 作業計画.txt`
3. `WORK_LOG.md`
4. `git status --short --branch`
5. `git log --oneline -5`

## 次に着手する作業

開発フェーズ1「解析方式の検証」を開始する。

1. Pythonと主要依存パッケージの対応バージョンを確認する。
2. 最小限のPythonプロジェクト設定を作成する。
3. Pillowを使用した画像読み込みと前処理を実装する。
4. JPEG、PNG、WebP、BMP、TIFF、GIFの読み込みを確認する。
5. EXIF回転、RGB変換、先頭フレーム選択、縦横比を維持した縮小を確認する。
6. 画像読み込み処理に対する小さな自動チェックを追加する。
7. その後、WD Tagger候補のONNX推論検証へ進む。

## 確定済み方針

- image2prompt独自のアプリとして実装する。
- Dataset Tag Editorは実装技術の参考資料としてのみ扱う。
- 初期UIはローカルWebアプリを候補とする。
- Apple Silicon MacとIntel Macを初期対象とする。
- Danbooruタグ生成はWD Tagger系モデルのローカル推論を第一候補とする。
- 自然言語モデルは比較検証後に決定する。
- 成人向けコンテンツ専用機能は初期版に含めない。
- Windows対応とスタンドアロン化はMVP後に検討する。

## 再開時点の注意事項

- モデルや依存パッケージを、検証前に大量追加しない。
- ダウンロードしたモデル、キャッシュ、生成結果はGitへ登録しない。
- 元画像を上書き、移動、削除しない。
- Gitへ公開する前にライセンスとGit作成者情報を確認する。
- リモートは未登録のため、確認なしにpushしない。
