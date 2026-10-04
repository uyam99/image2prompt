# 配布情報

基本バージョン：**0.2.0**。ソース固定タグ：`baseline-2026-10-04`。
ビルド対象commit：`d834f0396f7f2c6841bf5fb62dd44c2fb0e12df5`。
既存の `v0.2.0` タグは以前のソースを指し、今回の固定点とは異なります。

## 更新済み成果物

| 環境 | 成功したビルドrun | 配布ZIP | サイズ |
| --- | --- | --- | --- |
| macos-arm64 | [run 37191650080](https://github.com/uyam99/image2prompt/actions/runs/37191650080) | `image2prompt-macos-arm64.zip` | 508,508,776 bytes |
| windows-x64 | [run 37191651790](https://github.com/uyam99/image2prompt/actions/runs/37191651790) | `image2prompt-windows-x64.zip` | 864,538,340 bytes |

各runのArtifactsから取得できます。GitHubへのログインが必要な場合があります。
Artifactの保存期限は **2026-10-18** です。今回GitHub Releaseへの永続掲載は行っていません。
取得済みローカルZIPは `dist/test-builds/2026-10-04/` に保存しています。
同フォルダーの `README.txt`、`SHA256SUMS.txt`、`build-info.json`も参照してください。

## SHA-256（配布ZIP）

```text
5dde369c8a17f3cabed71a3d2c192e22c2bd381dfd5b937b492ee5a3b28c9ee5  image2prompt-macos-arm64.zip
842d88fb93dc84978d0ebdc4ef8ae90c31694b2f565f5888c58cafbdff03390a  image2prompt-windows-x64.zip
```

## 確認範囲

- Intel Mac：表示変更後のアプリを2026-10-04にユーザー確認済み。
- Apple Silicon／Windows：表示変更前の基準版はユーザー確認済み。今回の更新後の実機確認はこれからです。
- 今回はテスト版表示のみ削除し、解析処理・モデル・バージョン番号は維持しました。
- Apple Silicon CIはpytest 37件＋6 subtests、Windows CIは36件＋6 subtests、POSIX専用1件スキップ。
- 両OSのGitHub Artifactハッシュ、配布ZIP全件CRC、モデル・ランナー、アプリ本体とuvのarm64／x64形式を確認。
- 生成アプリ内のUIコードからテスト版表示が削除されていることを確認。
- Apple Siliconの署名検証はCIで成功。Mac版はadhoc署名で、Appleの公証は行っていません。

Intel版は `dist/image2prompt.app`、旧版バックアップは
`dist/backups/2026-10-04-before-ui-cleanup/image2prompt.app`です。
旧他OS成果物は `dist/test-builds/2026-09-26/` に保全しています。
