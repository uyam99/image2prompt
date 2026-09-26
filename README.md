# image2prompt

画像を解析し、画像生成向けのプロンプトを生成できるローカルアプリです。
Web UIでは同じ画像入力から、忠実度優先出力と任意のFlorence自然言語出力を
別タブで生成・編集できます。

- 忠実度優先形式
- Danbooruタグ形式
- Florence自然言語形式（任意）

SmolVLM自然言語形式とFlorence-2 ONNX詳細版は、開発・比較用CLIとして残しています。

## 現在の状態

安定版：`v0.2.0`

次版候補：`v0.3.0`（Florence自然言語形式の3プラットフォーム展開中）

標準画像の前処理、WD SwinV2 Tagger v3によるDanbooruタグ抽出、
タグを決定的に文章化する忠実度優先形式、Florence主体の編集可能な自然言語形式、
単一画像とフォルダー選択に対応したWeb UIを実装しています。忠実度優先形式は
引き続き既定・推奨出力です。

GitHubリポジトリ（Private）：[uyam99/image2prompt](https://github.com/uyam99/image2prompt)

## 対象環境

- Apple Silicon Mac
- Intel Mac
- Windows

通常の忠実度優先機能は3環境で実機確認済みです。Florence自然言語形式は
Intel Macで実機確認済みで、Apple Silicon版とWindows版は新しい配布成果物の
実機確認待ちです。

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
出力用のタグはアンダースコアを半角スペースへ変換します。`score_9`や`@_@`
など、アンダースコア自体に意味があるタグだけは元の表記を保ちます。

使用モデル：[SmilingWolf/wd-swinv2-tagger-v3](https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3)
（Apache-2.0）

## 忠実度優先プロンプト（推奨）

WD Taggerで信頼度0.50以上となったタグを、競合・重複を除去してから定型文へ
変換します。言語モデルによる推測を挟まないため、元画像にない物体や状態の
追加を抑えたい場合に使用します。外見と衣装は可能な範囲で同じ文へまとめ、
検出できた構図、カメラ視点、照明も自然文へ加えます。内部では人物、衣装、
動作、物体と、背景、フレーミング、カメラ、フォーカス、照明、画風を
分けて処理しますが、コピーするプロンプトには区分見出しを含めません。

```sh
uv run image2prompt-faithful /path/to/image.jpg
```

出力される`prompt`をComfyUIなどの画像生成環境へコピーして使用できます。
比較実験用に`--faithful-threshold`でしきい値を変更できますが、現在の推奨値は
3枚の固定画像で確認した0.50です。自然言語プロンプトは512トークンを基準と
しますが、上限にはせず、超過した文章もそのまま出力します。

任意の環境プリセットを追加する場合：

```sh
uv run image2prompt-faithful \
  --environment-preset anime_clean \
  /path/to/image.jpg
```

`photo_portrait`、`photo_street`、`photo_landscape`、`anime_clean`、
`anime_cinematic`を選択できます。既定値は`none`で、解析結果へ定型文を
追加しません。プリセットを選択した場合は手動指定を優先し、解析された画風と
プリセットの画風が重複しないようにします。

## Florence自然言語プロンプト（任意）

`MiaoshouAI/Florence-2-large-PromptGen-v2.0`の`<CAPTION>`と
`<DETAILED_CAPTION>`から自然言語本文を生成します。正確でない年齢・人種・国籍、
雰囲気、品質、透かしなどの推測文を決定的な規則で除き、画風を別欄へ分離します。

Web UIの「自然言語を生成」を押すと、次の内容を別々に編集できます。

- Florence主体の本文
- 画風
- WD補足（初期状態は空）
- 撮影・環境設定
- 上記を結合した最終プロンプト

初回実行時だけ、固定リビジョンのモデル約3.4GBと隔離されたPyTorch推論環境を
ユーザー領域へダウンロードします。2回目以降は同じ環境を再利用します。
Macでは`~/Library/Application Support/image2prompt/`、Windowsでは
`%APPDATA%\image2prompt\`配下へ保存します。アプリ本体の通常解析には
PyTorchを追加せず、モデルも配布物へ同梱しません。

使用モデル：
[MiaoshouAI/Florence-2-large-PromptGen-v2.0](https://huggingface.co/MiaoshouAI/Florence-2-large-PromptGen-v2.0)

## Florence-2詳細キャプション（開発・比較用）

Florence-2-base-ftの通常詳細版をCLIから比較できます。現在はWeb UIの
自然言語出力へ統合せず、スタンドアロン版にも同梱しません。PyTorchや
Node.jsは追加せず、既存のPython版ONNX Runtimeで実行します。

モデルはGitへ登録しないため、初回だけ次のファイルを取得します（約869 MB）。

```sh
uvx --from huggingface_hub hf download \
  onnx-community/Florence-2-base-ft \
  config.json preprocessor_config.json tokenizer.json tokenizer_config.json \
  onnx/vision_encoder.onnx \
  onnx/embed_tokens_int8.onnx \
  onnx/encoder_model_int8.onnx \
  onnx/decoder_model_merged_int8.onnx \
  --revision fac887a509cb8264d5639f04674c04977c65d937 \
  --local-dir models/transformers-js-cache/onnx-community/Florence-2-base-ft
```

```sh
uv run image2prompt-florence /path/to/image.jpg --max-new-tokens 512
```

生成上限は512トークンです。モデルが終了を判断した場合は上限前に完了します。
高詳細版は事実追加が増えたため使用しません。使用モデル：
[onnx-community/Florence-2-base-ft](https://huggingface.co/onnx-community/Florence-2-base-ft)
（MIT）

## SmolVLM自然言語プロンプト生成（参考）

PyTorchを使わず、既存のONNX Runtimeで動くSmolVLM-256Mの公式ONNX版を使用します。
初回だけ次のファイルを取得します（合計約540 MB）。

```sh
uvx --from huggingface_hub hf download \
  HuggingFaceTB/SmolVLM-256M-Instruct \
  config.json generation_config.json preprocessor_config.json \
  processor_config.json chat_template.json tokenizer.json \
  tokenizer_config.json special_tokens_map.json added_tokens.json \
  merges.txt vocab.json \
  onnx/vision_encoder.onnx \
  onnx/embed_tokens_int8.onnx \
  onnx/decoder_model_merged_int8.onnx \
  --revision 7e3e67edbbed1bf9888184d9df282b700a323964 \
  --local-dir models/smolvlm-256m-instruct
```

自然言語プロンプトをJSONで表示します。

```sh
uv run image2prompt-caption /path/to/image.jpg
```

被写体だけでなく、外見、衣装、姿勢、動作、背景、天候、照明、構図、色、
画風を含む詳細な説明を生成します。生成上限は初期値128トークンで、
`--max-new-tokens`により最大500トークンまで変更できます。

```sh
uv run image2prompt-caption /path/to/image.jpg --max-new-tokens 500
```

Intel Macでは512px入力、CPU実行を初期基準としています。使用モデル：
[HuggingFaceTB/SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)
（Apache-2.0）

## 3種類のプロンプトを同時生成

単一画像から忠実度優先形式、Danbooruタグ形式、SmolVLM自然言語形式を
同じJSONへ出力します。

```sh
uv run image2prompt-analyze /path/to/image.jpg
```

タグしきい値と自然言語の生成上限も指定できます。

```sh
uv run image2prompt-analyze \
  --general-threshold 0.35 \
  --character-threshold 0.85 \
  --max-new-tokens 500 \
  /path/to/image.jpg
```

## ローカルWeb UI

```sh
uv run image2prompt-web
```

表示された`http://127.0.0.1:7860`をブラウザーで開き、画像を選択して
「忠実度優先で解析」または「自然言語を生成」を押します。一般タグと
キャラクタータグのしきい値は、上部の「解析設定」を開くと変更できます。
画像入力と設定は両方式で共通です。

結果は「忠実度優先」と「自然言語（Florence）」のタブに分かれます。
忠実度優先タブではコピー用本文を先に表示し、Danbooruタグは折りたたみ欄へ
表示します。自然言語タブではコピー用の最終プロンプトを先に表示し、Florence本文、
画風、WD補足、撮影・環境設定は「詳細編集」から変更できます。Web UIでは
SmolVLMを実行しません。
「環境プリセット（任意）」からリアル人物、リアル・ストリート、
リアル・風景・建築、アニメ・クリーン、アニメ・シネマティックを選べます。
既定の「適用なし」は解析結果だけを使用します。
解析設定内は「タグ検出」と「環境プリセット」に分かれ、保存操作は下段へ
まとめています。
両方の表示枠には概算トークン数と基準値512を表示します。実際のトークン数は
ComfyUIで使用するモデルのトークナイザーによって変わるため、表示値は調整時の
目安として使用します。512を超えても警告や切り捨ては行いません。
外部公開や画像の送信は行いません。

解析設定の3項目は「解析設定を保存」を押すと保存され、次回起動時に復元されます。
Mac版の保存先は
`~/Library/Application Support/image2prompt/settings.json`です。
設定ファイルが存在しない場合や内容が壊れている場合は既定値を使用します。

「フォルダーから画像を選択」を開き、「画像フォルダーを選択」ボタン
からフォルダーを指定すると、直下の画像が縦横比を保ったサムネイルで並びます。
名前、更新日、種類による昇順・降順の並び替えに対応しています。macOSでは
名前順にFinder相当の標準比較を使用し、数字、記号、日本語を現在の
言語設定に合わせて並べます。
作業中にフォルダーの内容を変更した場合は「再読み込み」で一覧を更新できます。
選択中の画像が残っていれば、再読み込み後も選択を維持します。
フォルダーのドラッグ＆ドロップには対応していません。サムネイルを1枚選択して
してから目的の生成ボタンを押すと、その画像だけを解析します。`.DS_Store`など画像以外
のファイルは自動的に除外します。
フォルダー内の全画像を一括解析する機能はまだ実装していません。

## Intel Mac用スタンドアロン版（試作）

2026-09-26にユーザーから安定動作の報告を受け、9月6日のIntel版を今後の基準として
採用しました。Apple Silicon／Windows版の実機評価は別途必要です。

2026-09-06の運用テスト版では、通常／自然言語解析を順番に実行し、通常解析後に
ONNXの未使用作業領域を縮小します。自然言語処理はモデル準備に最大60分、
準備後の画像解析に最大10分を設け、制限時間超過とアプリ終了時に子プロセスを回収します。
アップロード・サムネイル用の一時画像はアプリごとの保存先を使い、正常終了時に削除します。
表示中の画像は再解析に必要なため、解析直後には削除しません。

不調が起きた場合は、発生時刻と次のログを残してください。
Finderの「移動」→「フォルダへ移動」で保存先を開けます。

`~/Library/Application Support/image2prompt/logs/`

`image2prompt.log`に処理の開始・終了・失敗・子プロセス終了コード・親プロセスの
最大RSSを記録します。1ファイル2MiB、過去3ファイルを保持します。
最大RSSは起動後の最高値で、現在使用量ではありません。画像や生成結果全体は記録対象にしません。

Pythonやuvを利用者側へ要求しないone-folder型の`.app`を作成します。

```sh
zsh packaging/build_macos.sh
```

生成先は`dist/image2prompt.app`です。ダブルクリックすると専用のアプリ内
ウィンドウを開き、外部ブラウザーは使用しません。Python実行環境とWD Tagger
モデル、自然言語用の`uv`とFlorenceランナーを同梱します。Florenceモデルと
PyTorchは含めません。現在のIntel Mac実測サイズは約854MBです。専用アイコンは
`packaging/assets/image2prompt.icns`を使用します。

現在はローカル検証用のadhoc署名です。他のMacへ配布する前に正式なコード署名と
notarizationが必要です。Apple Silicon版はarm64環境で同じスクリプトを実行して
別途検証します。ビルドにはネットワーク接続が必要ですが、生成済みアプリの
解析はローカルだけで動作します。

GitHubではActionsの「Build macOS Apple Silicon standalone」を手動実行すると、
Apple Silicon runner上でarm64版を生成します。成功後、runのArtifactsから
`image2prompt-macos-arm64`をダウンロードできます。成果物の保存期間は14日です。
初回ビルドは
[Actions run 30740705505](https://github.com/uyam99/image2prompt/actions/runs/30740705505)
で通常解析版の生成と実機確認に成功しました。自然言語対応版は、CIで新しい成果物を
生成した後、初回ダウンロード、再利用、生成、正常終了をApple Silicon実機で確認します。

## Windows用スタンドアロン版（試作）

Windows x64環境で次を実行します。PyInstallerはクロスコンパイルできないため、
Mac上ではWindows版を生成できません。

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_windows.ps1
```

生成先は`dist\image2prompt\image2prompt.exe`です。配布時はexe単体ではなく、
`dist\image2prompt`フォルダー全体を渡します。Python実行環境、WD Taggerモデル、
専用アイコン、`uv.exe`、Florenceランナーを同梱し、外部ブラウザーを開かず
専用ウィンドウで動作します。利用者側にPythonやuvは不要です。Florenceモデルと
PyTorchは初回の自然言語生成時にユーザー領域へ取得します。

表示にはMicrosoft Edge WebView2 Runtimeを使用します。Windows 11には同梱され、
大半のWindows 10環境にも導入済みですが、未導入環境では
[Microsoft公式WebView2ページ](https://developer.microsoft.com/en-us/microsoft-edge/webview2)
からEvergreen Runtimeを先にインストールします。設定は
`%APPDATA%\image2prompt\settings.json`へ保存します。

GitHubではActionsの「Build Windows standalone」を手動実行すると、同じビルドを
Windows runner上で行います。成功後、runのArtifactsから
`image2prompt-windows-x64`をダウンロードできます。成果物の保存期間は14日です。
Windows x64での初回ビルドは
[Actions run 30740190367](https://github.com/uyam99/image2prompt/actions/runs/30740190367)
で通常解析版の生成と実機確認に成功しました。自然言語対応版は、CIで新しい成果物を
生成した後、初回ダウンロード、再利用、生成、正常終了をWindows実機で確認します。

## 次のマイルストーン

1. JPEG、PNG、WebP、BMP、TIFF、GIFの読み込み確認：完了
2. EXIF回転、RGB変換、縦横比を維持した画像前処理：完了
3. WD Tagger候補のローカル推論：完了
4. 単一画像Web UI：完了
5. 自然言語モデル候補の比較：Florence-2-large PromptGenを任意機能へ採用
6. フォルダー内の画像一覧と単一選択：完了
7. 忠実度優先プロンプト生成：完了
8. 複数画像の一括処理、進捗表示、CSV出力：保留
9. Intel Mac用スタンドアロン版：専用ウィンドウ・専用アイコンで実機確認完了
10. Windows用スタンドアロン版：通常解析は実機確認完了、自然言語対応版は実機確認待ち
11. Apple Silicon用スタンドアロン版：通常解析は実機確認完了、自然言語対応版は実機確認待ち

詳細は[作業計画](./image2prompt%20作業計画.txt)を参照してください。

## 進捗記録

- 作業が進んだ段階で[WORK_LOG.md](./WORK_LOG.md)へ追記します。
- 作業を中断する際は[NEXT_RESUME_POINT.md](./NEXT_RESUME_POINT.md)を更新します。

## ライセンス

未決定です。公開前にライセンスを選定します。
