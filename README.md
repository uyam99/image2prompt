# image2prompt

画像を解析し、画像生成向けの英語プロンプトを生成・編集するローカルアプリです。
忠実度優先形式、Danbooruタグ形式、任意のFlorence自然言語形式に対応します。

## 基本バージョン

基本バージョンは **0.2.0** です。Intel Mac、Apple Silicon Mac、Windows x64で
ユーザーの実行確認が完了した安定性対策版を基準にしています。
2026-10-04にテスト版の表示を削除しました。解析処理は変更していません。
今回の固定点はGitタグ `baseline-2026-10-04` で識別します。
既存の `v0.2.0` タグは以前のソースを指すため、今回の固定点とは区別してください。

リポジトリ：[uyam99/image2prompt](https://github.com/uyam99/image2prompt)

## 対象環境と起動

| 環境 | 起動方法 |
| --- | --- |
| Intel Mac | Intel用ZIPを展開し、`image2prompt.app`を起動 |
| Apple Silicon Mac | arm64用ZIPを展開し、`image2prompt.app`を起動 |
| Windows x64 | ZIPをフォルダーごと展開し、`image2prompt.exe`を起動 |

配布物にはPython、WD Taggerモデル、自然言語処理用のuvを同梱しています。
利用者によるPythonやuvのインストールは不要です。Windowsではexeだけを移動せず、
同梱フォルダーを保持してください。Macも同梱物を削除しないでください。

Apple Silicon／WindowsのZIPは、[GitHub Actions](https://github.com/uyam99/image2prompt/actions)
の成功したrunのArtifactsから取得できます。Artifactの保存期間は14日です。
今回の表示変更後の成果物情報は [配布情報](docs/DISTRIBUTION.md) に記載します。

Macアプリはadhoc署名で、Appleの公証は行っていません。
Windowsの表示にはMicrosoft Edge WebView2 Runtimeを使用します。
未導入の場合は[Microsoft公式ページ](https://developer.microsoft.com/en-us/microsoft-edge/webview2)
から導入してください。

## 使い方

1. 画像をアップロードするか、「フォルダーから画像を選択」で画像を1枚選びます。
2. 「忠実度優先」または「自然言語（Florence）」から生成します。
3. 結果を確認・編集し、最終プロンプトを画像生成環境へコピーします。

JPEG/JPG、PNG、WebP、BMP、TIFF/TIF、GIFに対応します。GIFは先頭フレームを使用します。
元画像は変更しません。フォルダー一覧は名前・更新日・種類で並べ替えられ、
「再読み込み」で更新できます。フォルダーの一括解析は未実装です。

### 忠実度優先（既定・推奨）

WD SwinV2 Tagger v3で検出したタグを、競合・重複を整理して決定的に文章化します。
言語モデルによる推測を抑えた出力に向いています。Danbooruタグ形式も利用できます。
「解析設定」でタグのしきい値と任意の環境プリセットを変更し、保存できます。

### 自然言語（Florence）

初回生成時にモデル約3.4GBとPyTorch推論環境をダウンロードします。
初回の準備にはネットワーク接続と保存容量が必要です。準備後は同じ環境を再利用します。
本文、画風、WD補足、撮影・環境設定を「詳細編集」で調整できます。
WD補足は初期状態では空で、必要なときに追加します。
画像にない内容が含まれる場合があるため、生成結果を確認してから使用してください。
512トークン表示は目安で、文章の切り捨ては行いません。

## 保存先と終了

| 環境 | 設定・モデル・ログの保存先 |
| --- | --- |
| macOS | `~/Library/Application Support/image2prompt/` |
| Windows | `%APPDATA%\image2prompt\` |

設定は `settings.json`、ログは `logs/image2prompt.log` に保存します。
ログは最大2MiB、過去3ファイルを保持します。画像や生成結果全体はログへ記録しません。
画像解析はローカルで行います。モデル準備に最大60分、準備後の自然言語解析に最大10分を設け、
タイムアウトとアプリ終了時に子プロセスを回収します。専用の一時画像は正常終了時に削除します。

不調時はOS、発生時刻、解析モード、画像サイズ、表示内容とログを確認してください。

## 開発資料

- [ソース実行・モデル比較・ビルド](docs/DEVELOPMENT.md)
- [配布情報](docs/DISTRIBUTION.md)
- [作業履歴](WORK_LOG.md)
- [次回の再開ポイント](NEXT_RESUME_POINT.md)

## 使用モデルとライセンス

- [SmilingWolf/wd-swinv2-tagger-v3](https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3)：Apache-2.0
- [MiaoshouAI/Florence-2-large-PromptGen-v2.0](https://huggingface.co/MiaoshouAI/Florence-2-large-PromptGen-v2.0)：モデル提供元のライセンスに従います。

本リポジトリのソースライセンスは未設定です。公開のみをもって再利用・再配布の許諾を付与するものではありません。
モデルと依存ライブラリはそれぞれのライセンスに従います。
