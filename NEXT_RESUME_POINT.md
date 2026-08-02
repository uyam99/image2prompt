# 次回の再開ポイント

更新日：2026-08-02

## 作業ルート

`/Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt`

以後の編集、Git操作、テスト実行はこのフォルダーを基準にする。

## 再開時に最初に確認するもの

1. `README.md`
2. `image2prompt 作業計画.txt`
3. `WORK_LOG.md`
4. `git status --short --branch`
5. `git log --oneline -5`

## 継続テストの実行方法

作業ルートへ移動し、Web UIを起動する。

```sh
cd /Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt
uv sync
uv run image2prompt-web
```

ブラウザーで`http://127.0.0.1:7860`を開き、画像を解析した後、
「忠実度優先形式（推奨・ComfyUI向け）」をコピーして画像生成へ使用する。

CLIだけで忠実度優先形式を生成する場合：

```sh
uv run image2prompt-faithful /path/to/image.jpg
```

3形式をまとめて比較する場合：

```sh
uv run image2prompt-analyze --max-new-tokens 500 /path/to/image.jpg
```

コード変更後の確認：

```sh
uv run python -m unittest
uv run ruff check .
```

## 現在の状態

現行機能は安定版`v0.2.0`として区切る。ユーザーが実際の画像フォルダーと
ComfyUIで継続使用し、希望する動作に問題がないことを確認した。

統合CLI、単一画像Web UI、フォルダー内画像の一覧と単一選択、並び替え、
再読み込み、解析設定の保存、忠実度優先プロンプトは完了している。
GitHubへコミットやタグを反映する場合は、実行前にユーザー確認を取る。

## 次に着手する作業

予定した機能追加はいったん止め、現行版を継続使用する。不足や誤認が
見つかった場合だけ、元画像、使用プロンプト、生成結果、使用モデルを一組に
して確認し、競合・除外規則を最小限調整する。

複数画像の一括処理、進捗表示、CSV出力、Florence-2統合、Windows対応、
スタンドアロン化は、具体的な必要が生じるまで保留する。

Finderの更新日順を比較する場合は、Finderの「グループ分け」と「表示順序」を
両方とも「変更日」にし、アプリの「更新日・降順」と比較する。これはmacOSの
表示設定に関するTipsであり、アプリへ追加対応しない。

## 確定済み方針

- image2prompt独自のアプリとして実装する。
- Dataset Tag Editorは実装技術の参考資料としてのみ扱う。
- 初期UIはローカルWebアプリを候補とする。
- Apple Silicon MacとIntel Macを初期対象とする。
- Python 3.12を両Mac共通の基準環境とする。
- 標準画像の前処理にはPillow 11系を使用する。
- Danbooruタグ生成にはWD SwinV2 Tagger v3の固定リビジョンを使用する。
- Intel MacではONNX Runtime 1.20.1のCPU実行を基準とする。
- 自然言語モデルはSmolVLM-256Mの公式ONNX版をMVPへ採用する。
- 自然言語生成は512px入力をIntel Macの初期基準とする。
- 自然言語生成は既定128トークン、指定時は最大500トークンとする。
- UIはGradio 5.49.1を使用し、`127.0.0.1`だけで待ち受ける。
- UI起動中は2つのモデルを再利用する。
- フォルダー入力では一覧から1枚を選択し、その画像だけを解析する。
- フォルダー指定はmacOSのFinder選択ボタンを使用し、実フォルダーのパスを
  保持する。フォルダーのドラッグには対応しない。
- 一覧は名前、更新日、種類による昇順・降順の並び替えと再読み込みに対応する。
- macOSの名前順にはFinder相当の`localizedStandardCompare`を使用し、
  現在の言語設定に合わせて数字、記号、日本語を並べる。
- フォルダー走査は直下だけを対象とし、サブフォルダーは再帰走査しない。
- 外部フォルダーの元画像はGradioへ直接公開せず、一覧表示用の縮小画像だけを
  システム一時領域へ生成する。解析には元画像の実パスを使用する。
- フォルダー内の画像以外のファイルは自動的に除外する。
- フォルダー内の全画像を一括解析する機能は後回しとする。
- 解析設定は保存ボタンでユーザー別のJSONへ保存し、次回起動時に復元する。
- 成人向けコンテンツ専用機能は初期版に含めない。
- Windows対応とスタンドアロン化はMVP後に検討する。

## 再開時点の注意事項

- モデルや依存パッケージを、目的なく追加しない。
- 最新ONNX RuntimeはIntel Mac用wheelを提供しないため、1.20.1の固定を
  実機検証なしに更新しない。
- SmolVLMのint8視覚エンコーダーはIntel CPUで動かないため使用しない。
- PyTorchと`torchvision`はIntel Macの共通経路へ追加しない。
- 比較用SmolVLM-500Mは`models/smolvlm-500m-instruct`にあり、
  Git追跡対象外である。現時点ではアプリへ組み込まない。
- Florence-2比較モデルは`models/transformers-js-cache`にあり、
  Git追跡対象外である。キャッシュ容量は約899MB。
- 最新`onnxruntime-node`はmacOS Intel x64を実行できないため、
  Florence-2の実験では1.20.1を使用した。
- Florence-2のint8視覚エンコーダーもIntel CPUでは使用しない。
- 自然言語品質では、情報量よりも存在しない物体・状態を追加しないことを
  優先する。
- ComfyUIでの初回比較には、Web UIの忠実度優先形式をそのまま使用する。
- 忠実度優先形式の推奨しきい値は0.50とし、実生成結果が揃うまで変更しない。
- ダウンロードしたモデル、キャッシュ、生成結果はGitへ登録しない。
- 元画像を上書き、移動、削除しない。
- Publicへ変更する前にライセンスとGit作成者情報を確認する。
- GitHubリモートは`origin`として登録済み。今後も確認なしにpushしない。
- 2026-07-25終了時点で通常の`git push`は成功しているが、
  `gh auth status`はGitHub CLI用トークンを無効と判定した。PR作成など
  `gh`のAPI操作が必要になった場合は`gh auth login -h github.com`をやり直す。
