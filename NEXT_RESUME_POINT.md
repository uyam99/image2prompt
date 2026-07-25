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

## 次に着手する作業

統合CLI、単一画像Web UI、フォルダー内画像の一覧と単一選択、解析設定の保存は
完了した。ここまでを基本版`v0.1.0`として固定し、GitHubのPrivateリポジトリ
`uyam99/image2prompt`へ保存した。

自然言語生成で元画像にない物体や状態を追加する問題への現段階の対策として、
WDタグを信頼度0.50で整理し、言語モデルを介さず決定的に文章化する
「忠実度優先形式」を実装した。

ユーザーによるComfyUIでの初回テスト生成では、これまでの自然言語形式の中で
最も良い感触が得られた。元画像との完全一致ではなく、参考画像の主要な要点を
抽出する用途として有効と判断した。

次は忠実度優先形式を標準候補として使い続け、別の画像でも次の点を確認する。

1. 主要な被写体、姿勢、動作、手に持つ物が抽出できるか。
2. 元画像にない物体や衣装が追加されていないか。
3. 背景情報が不足しすぎていないか。
4. 不足または誤りがあれば、画像名、使用モデル、生成画像、使用プロンプトを
   記録して競合・除外規則だけを最小限調整する。

Florence-2の通常詳細版は、タグで不足する背景と構図の補助候補として残す。
高詳細版は誤った詳細を追加するため使用しない。Transformers.jsによる
Florence-2経路にはONNX Runtime 1.20.1向けの互換処理が必要なので、
現時点ではアプリへ組み込まない。

比較対象は次の3画像へ固定する。

- `629902723_18312937399268168_9206735518451670517_n.jpg`
- `b22377e6c91affb9e79eb1e890155420.jpg`
- `d9b4569924bfc2f1b1655ca39e3e0042.jpg`

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
- フォルダー指定はFinder選択ボタンを使用し、フォルダーのドラッグには
  対応しない。
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
