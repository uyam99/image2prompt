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

WD TaggerとSmolVLM-256Mの個別推論、および2種類のプロンプトを同じJSONへ
出力する統合CLIは完了した。次は統合出力のユーザー確認とWeb UIへ進む。

1. ユーザー環境で`uv run image2prompt-analyze /path/to/image.jpg`を実行する。
2. Danbooruタグと自然言語が同じJSONへ出力されることを確認する。
3. Gradioによる単一画像MVPを作る。
4. 画像選択、プレビュー、しきい値、生成上限、実行ボタンを配置する。
5. 2種類のプロンプトを個別欄へ表示し、コピーできるようにする。
6. UI起動中はモデルを保持し、2回目以降の読み込みを省く。

## 確定済み方針

- image2prompt独自のアプリとして実装する。
- Dataset Tag Editorは実装技術の参考資料としてのみ扱う。
- 初期UIはローカルWebアプリを候補とする。
- Apple Silicon MacとIntel Macを初期対象とする。
- Python 3.12を両Mac共通の基準環境とする。
- 標準画像の前処理にはPillow 12系を使用する。
- Danbooruタグ生成にはWD SwinV2 Tagger v3の固定リビジョンを使用する。
- Intel MacではONNX Runtime 1.20.1のCPU実行を基準とする。
- 自然言語モデルはSmolVLM-256Mの公式ONNX版をMVPへ採用する。
- 自然言語生成は512px入力をIntel Macの初期基準とする。
- 自然言語生成は既定128トークン、指定時は最大500トークンとする。
- 成人向けコンテンツ専用機能は初期版に含めない。
- Windows対応とスタンドアロン化はMVP後に検討する。

## 再開時点の注意事項

- モデルや依存パッケージを、目的なく追加しない。
- 最新ONNX RuntimeはIntel Mac用wheelを提供しないため、1.20.1の固定を
  実機検証なしに更新しない。
- SmolVLMのint8視覚エンコーダーはIntel CPUで動かないため使用しない。
- PyTorchと`torchvision`はIntel Macの共通経路へ追加しない。
- ダウンロードしたモデル、キャッシュ、生成結果はGitへ登録しない。
- 元画像を上書き、移動、削除しない。
- Gitへ公開する前にライセンスとGit作成者情報を確認する。
- リモートは未登録のため、確認なしにpushしない。
