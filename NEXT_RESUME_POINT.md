# 次回の再開ポイント

更新日：2026-09-26

Intel版のユーザー運用確認は完了。安定性対策の製品ソースはローカルcommit `a3d7887`に確定済み。
次はGitHubへのpushとApple Silicon／Windowsビルドの実行。自動承認レビューにより明示承認待ち。

## 作業ルート

`/Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt`

以後の編集、Git操作、テスト実行はこのフォルダーを基準にする。

## 運用結果と固定対象

2026-09-26、ユーザーから「今のところは安定して動作」「このバージョンで固定しても
大丈夫」と報告を受けた。Intel版の運用確認待ちを解除し、9月6日の安定性対策版を
今後の基準として採用する。使用回数・連続稼働時間の数値は未取得で、全条件での無再発を
保証する評価ではない。Apple Silicon／Windowsの実機確認は別途必要。

対象は`dist/image2prompt.app`。画面表示「運用テスト版：2026-09-06」とパッケージの
バージョン`0.2.0`は維持している。今回は機能変更・再ビルド・リリース番号変更を行わず、
実際に運用確認されたアプリを基準にする。旧版バックアップは
`dist/backups/2026-09-06-before-stability/image2prompt.app`。

採用対象は共通キュー、保存ログ、準備／解析別タイムアウトと子プロセス回収、
専用一時画像の終了時削除、WD作業メモリ縮小、自然言語編集イベントの整理。
根拠は`INVESTIGATION_2026-09-06.md`と`WORK_LOG.md`を参照する。

## 次に進める作業

1. GitHub `uyam99/image2prompt`の`main`へのpushと、Apple Silicon／Windowsの
   `workflow_dispatch`についてユーザーの明示承認を得る。実行を試みたが、自動承認レビューで
   共有リモート変更・ソース送信・CI起動への明示承認が必要とされ、コマンド実行前に拒否された。
2. 承認後に最新の`origin/main`を確認し、製品commit `a3d7887`と引き継ぎ文書をpushする。
   両workflowを同じリビジョンで実行し、runのhead SHAを確認する。
3. 成果物を取得してバンドル内容を確認し、各OSで起動・解析・画像選択・編集・終了の
   ユーザー実機評価へ進む。旧runの単純な再実行は避ける。

`a3d7887`は共通キュー、ログ、タイムアウト・終了処理、一時画像管理、WDのarena縮小を含む。
`wd_tagger.py`の比較モデル識別、`tests/test_wd_tagger.py`、`experiments/`は含めていない。
これら研究用の差分は元の作業ツリーに未コミットのまま残している。

製品ソースの切り出しに対してpytest 37件＋6 subtests、Ruffに成功。
実画像の通常／自然言語各1回も、運用済みIntelアプリとSHA-256が一致した（5.86秒／54.55秒）。
検証証跡は`outputs/diagnostics/2026-09-26/product-tests.log`、`product-inference.jsonl`。
Intelアプリの再ビルドは行っておらず、9月6日の運用済みアプリを保持している。

再発時は時刻・画像サイズ・モード・表示内容と
`~/Library/Application Support/image2prompt/logs/image2prompt.log`（`.1`〜`.3`も含む）を
照合する。ログの最大RSSは起動後の最高値であり、現在使用量ではない。

## 保留中：Apple Silicon／Windows成果物の取得

9月26日にGitHubへ接続し、Artifact一覧0件、最新runが以下の8月23日の失敗runであることを
確認した。新しいビルドは承認待ちで未実行。ストレージ上限の解消はまだ未確認。
旧runには今回の安定性対策が含まれないため、更新版を配布する場合はビルド対象の
リビジョンを確定してから実行する。

対象run（commit `4ae1e34`）：

- Apple Silicon：`32625753202`
- Windows：`32625753217`

成果物：

- `image2prompt-macos-arm64`
- `image2prompt-windows-x64`

8月23日時点で両runはattempt 2まで、テスト、アプリ生成、バンドル検証に成功し、最後のArtifact
アップロードだけ容量上限で失敗している。Artifactsの保存期間は14日。生成後は
ユーザーが各実機で以下を確認する。

再開時の順序：

1. GitHub Actionsの現在の容量・Artifact一覧・workflowの状態を確認する。
2. ビルド対象のリビジョンを確定し、両OSのworkflowを実行する。
3. 両runのArtifactアップロード成功を確認する。
4. 2つのArtifactをダウンロードし、macOSはZIP内の`.app`、Windowsはone-folder一式が
   含まれることを確認する。
5. ユーザーへ実機テストを引き渡す。

## Apple Silicon実機テスト

1. ZIPを展開し、`image2prompt.app`をFinderから起動する。
2. 「忠実度優先」「自然言語（Florence）」の2タブが表示されることを確認する。
3. 単体アップロードとフォルダー選択から忠実度優先解析を実行する。
4. 「自然言語を生成」を初めて押し、推論環境と約3.4GBのモデル取得が完了することを確認する。
5. 2回目以降は取得済み環境を再利用することを確認する。
6. 最終プロンプト、Florence本文、画風、空のWD補足、撮影設定が表示されることを確認する。
7. 詳細編集とWD補足の追加・解除が最終プロンプトへ反映されることを確認する。
8. アプリ終了後にプロセスとTCP 7860／7861が残らないことを確認する。

## Windows実機テスト

1. Artifactをフォルダーごと展開する。`image2prompt.exe`だけを取り出さない。
2. `image2prompt.exe`を起動し、専用ウィンドウと2つの出力タブを確認する。
3. 単体アップロード、フォルダー選択、忠実度優先解析を確認する。
4. 自然言語の初回ダウンロードと2回目以降の再利用を確認する。
5. Florence本文、画風、空のWD補足、撮影設定、最終プロンプトを確認する。
6. 詳細編集とWD補足の追加・解除を確認する。
7. 終了後に`image2prompt.exe`と子プロセス、TCP 7860／7861が残らないことを確認する。

Windows 10で専用ウィンドウが開かない場合は、Microsoft Edge WebView2 Runtimeの
有無を先に確認する。

## 現在完了している作業

- 忠実度優先形式は安定版`v0.2.0`の既定・推奨出力として維持した。
- Florence自然言語形式を任意機能として採用した。
- 画像入力と解析設定を共有し、結果を忠実度優先／自然言語タブへ整理した。
- 自然言語タブは最終プロンプトを先に表示し、編集欄を「詳細編集」へまとめた。
- `image2prompt/florence_runner.py`を製品用の隔離実行スクリプトとして追加した。
- Windowsでバンドルされた`bin/uv.exe`を検出できるようにした。
- macOS／WindowsビルドへFlorenceランナーと各OS用`uv`を追加した。
- CIの成果物検証へランナーと`uv`の存在確認を追加した。
- Intel x86_64版`dist/image2prompt.app`を再ビルドし、実起動と自然言語生成を確認した。
- 9月6日の安定性対策を反映し、unittest 37件、pytest 38件＋6 subtests、Ruffに成功した。

Intel版は約854MB、アプリ本体と同梱`uv`はx86_64、adhoc署名検証済み。
FlorenceモデルとPyTorchは同梱していない。9月6日の更新版アプリで実画像を2往復し、
全4回の出力が更新前と一致した。自然言語は38.68／31.25秒、再起動後の通常解析は2.13秒。
処理中のネイティブ終了経路と再起動後の終了で、子プロセス・専用一時フォルダー・
TCP 7860／7861の残留がないことを確認した。9月26日にユーザーから安定動作の報告を受けた。
検証証跡は`outputs/diagnostics/2026-09-06/`の`app_inference_check.jsonl`、
`app_runtime_verified.log`、`app_close_during_inference.log`、`build_macos_stability.log`を参照する。

## 継続検証コマンド

```sh
cd /Volumes/HDD8TB/WORK/codex-prj/image2prompt/image2prompt
UV_CACHE_DIR=.cache/uv uv run python -m unittest
UV_CACHE_DIR=.cache/uv uv run ruff check .
git diff --check
git status --short --branch
```

Intel版の再ビルド：

```sh
zsh packaging/build_macos.sh
codesign --verify --deep --strict dist/image2prompt.app
```

## 配布境界

- Florenceモデル約3.4GBとPyTorchはアプリへ同梱しない。
- 初回の自然言語生成時だけネットワーク接続を必要とする。
- Macの保存先は`~/Library/Application Support/image2prompt/`、Windowsは
  `%APPDATA%\image2prompt\`である。
- WD補足は自動追加せず、初期状態を空にする。
- 忠実度優先形式を自然言語形式で置き換えない。
- ONNX変換、MPS最適化、複数画像一括処理、インストーラー、自動更新は保留する。
- 不採用比較用の`experiments/`は削除せずローカルに保全するが、製品ランタイムは参照しない。

## Git状態

製品commitは`a3d7887`（fix: stabilize repeated image analysis and runtime cleanup）。
9月26日のfetch時点で`origin/main`は`a301555711ea7d247609bac2f14661220d0df1ac`。
その後のpushは自動承認レビューでコマンド実行前に拒否され、製品変更はまだリモートへ送っていない。
この再開記録と作業記録は別の文書commitとしてローカルに保存する。

`image2prompt/wd_tagger.py`、`tests/test_wd_tagger.py`、`experiments/`の比較研究差分は
未コミットのまま保全。モデル、キャッシュ、生成結果、`dist/`はGit追跡対象外。
切り出した製品ソースと研究差分の退避patch、検証証跡は
`outputs/diagnostics/2026-09-26/`（Git対象外）に保存した。
