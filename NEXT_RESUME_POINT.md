# 次回の再開ポイント

更新日：2026-10-04

## 基本バージョン

基本バージョン0.2.0を固定する。今回のソース固定点は`baseline-2026-10-04`。
既存の`v0.2.0`タグは過去のソースを指すため変更しない。
Intel／Apple Silicon／Windowsのユーザー実行確認は完了。
テスト版表示を削除したIntel版もユーザー確認済み。

## 今回の作業

- UIのテスト版表示を削除。解析処理・モデル・バージョン番号は維持。
- READMEを利用者向けに整理し、開発説明を`docs/DEVELOPMENT.md`へ分離。
- Apple Silicon／Windows再ビルド・成果物取得・検証、GitHub Public化は完了。
- 製品commitと基本版タグは`d834f03`。その後の文書更新は製品ソースを変更しない。
- 最新ZIPは`dist/test-builds/2026-10-04/`。run、サイズ、SHA-256は`docs/DISTRIBUTION.md`へ記録済み。
- GitHub Artifactは2026-10-18まで。ローカルZIPは残る。GitHub Releaseへの永続掲載は未実施。
- リポジトリのソースライセンスは未設定。
- 公開基準ソースのunittest 36件、Ruff、差分チェックに成功。

## 保全対象

Intelアプリ：`dist/image2prompt.app`。
表示変更前のバックアップ：`dist/backups/2026-10-04-before-ui-cleanup/image2prompt.app`。
旧他OS成果物：`dist/test-builds/2026-09-26/`。
研究差分：`image2prompt/wd_tagger.py`、`tests/test_wd_tagger.py`、`experiments/`。
これら研究差分は製品commitに含めず、元の作業ツリーへ未コミットのまま保持する。
モデル、キャッシュ、診断ログ、distはGit対象外。
作業ルートはリポジトリのルートディレクトリ。

## 配布境界

Florenceモデル約3.4GBとPyTorchは初回の自然言語生成時に取得する。
忠実度優先を既定・推奨とし、WD補足は初期状態を空にする。
複数画像一括処理、モデル変更、インストーラー、自動更新は今回の範囲に含めない。

## 次の確認

更新したApple Silicon／Windowsアプリの実機確認結果を受け取る。
不調時はOS、発生時刻、解析モード、画像サイズと保存ログで切り分ける。
今回のビルド・公開化の最終状態はWORK_LOG.mdと配布情報を参照する。
