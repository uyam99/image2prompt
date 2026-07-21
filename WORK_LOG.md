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
