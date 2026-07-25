# 次回の再開ポイント

更新日：2026-07-25

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

開発フェーズ1の次段階「WD TaggerのONNX推論検証」を開始する。

1. Python 3.12環境へONNX Runtime 1.20.1を導入できることを確認する。
2. Intel Macで利用される実行プロバイダーを確認する。
3. WD Tagger候補モデルと`selected_tags.csv`をキャッシュへ取得する。
4. `prepare_image()`の結果をモデル用配列へ変換する。
5. 1枚の画像からタグ名と信頼度を取得する。
6. ratingタグを分離し、一般タグとキャラクタータグを分類する。
7. しきい値以上のタグをカンマ区切りで表示する最小CLIを作成する。
8. 代表画像で処理時間とタグ内容を記録する。

## 確定済み方針

- image2prompt独自のアプリとして実装する。
- Dataset Tag Editorは実装技術の参考資料としてのみ扱う。
- 初期UIはローカルWebアプリを候補とする。
- Apple Silicon MacとIntel Macを初期対象とする。
- Python 3.12を両Mac共通の基準環境とする。
- 標準画像の前処理にはPillow 12系を使用する。
- Danbooruタグ生成はWD Tagger系モデルのローカル推論を第一候補とする。
- 自然言語モデルは比較検証後に決定する。
- 成人向けコンテンツ専用機能は初期版に含めない。
- Windows対応とスタンドアロン化はMVP後に検討する。

## 再開時点の注意事項

- モデルや依存パッケージを、検証前に大量追加しない。
- 最新ONNX RuntimeはIntel Mac用wheelを提供しないため、そのまま更新しない。
- ONNX Runtime 1.20.1のUniversal2 wheelを最初の候補として検証する。
- ダウンロードしたモデル、キャッシュ、生成結果はGitへ登録しない。
- 元画像を上書き、移動、削除しない。
- Gitへ公開する前にライセンスとGit作成者情報を確認する。
- リモートは未登録のため、確認なしにpushしない。
