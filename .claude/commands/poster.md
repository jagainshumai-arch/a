# Threads ポスター 📤

post-queue.md を読んで、一番上の投稿をThreadsに投稿してください。

## 手順

1. `threads_automation/data/post-queue.md` の一番上の投稿を取得

2. 投稿前の最終チェック
   □ `threads_automation/knowledge/07_ng-rules.md` に違反してないか？
   □ ハッシュタグ（#）が含まれていないか？
   □ AI感のある表現がないか？

3. Threads APIで投稿する
   - まず本文を投稿
   - 次にコメント欄用のテキストをセルフリプライで投稿

4. 投稿が完了したら
   - post-queue.md から投稿済みの分を削除
   - `threads_automation/data/post-history.md` に投稿日時とpost_idを追記

## 注意
- 1回の実行で1投稿だけ。複数投稿しない
- APIエラーが出たら1回だけリトライ。2回失敗したら止める
- 投稿済みの内容を二重投稿しないこと
- **投稿前に必ずユーザーの承認を求める**（自動投稿しない）

## 引数
$ARGUMENTS — "all" で全件投稿（間隔5分）。未指定時は1件のみ。
