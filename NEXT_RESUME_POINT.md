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

WD Taggerの単一・複数画像推論と、SmolVLM-256Mによる自然言語プロンプトの
最小生成は完了した。次は自然言語出力のユーザー確認と単一画像MVPへ進む。

1. ユーザー環境で詳細化後の`uv run image2prompt-caption /path/to/image.jpg`
   を実行する。
2. 被写体、服装、動作に加え、背景、天候、照明、構図、色、画風が
   十分に含まれるか確認する。
3. SmolVLMの省略傾向が許容範囲なら暫定採用を確定する。
4. WD TaggerとSmolVLMを1回の操作で実行する単一画像CLIを作る。
5. 2種類のプロンプトと個別処理時間を同じJSONへ出力する。
6. その後、Gradioによる単一画像MVPへ進む。

## 確定済み方針

- image2prompt独自のアプリとして実装する。
- Dataset Tag Editorは実装技術の参考資料としてのみ扱う。
- 初期UIはローカルWebアプリを候補とする。
- Apple Silicon MacとIntel Macを初期対象とする。
- Python 3.12を両Mac共通の基準環境とする。
- 標準画像の前処理にはPillow 12系を使用する。
- Danbooruタグ生成にはWD SwinV2 Tagger v3の固定リビジョンを使用する。
- Intel MacではONNX Runtime 1.20.1のCPU実行を基準とする。
- 自然言語モデルはSmolVLM-256Mの公式ONNX版を暫定候補とする。
- 自然言語生成は512px入力をIntel Macの初期基準とする。
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
