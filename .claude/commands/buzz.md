# Threads バズ収集・分析 🔥

伸びている投稿（バズ）を収集・蓄積し、再現可能な「勝ちパターン」を抽出するエージェント。
シロウ式の「バズ収集 → 構造化 → 抽出 → 投稿に活用」の複利サイクルを回す。

## データの流れ

```
収集（手動 or 取り込み）
  → data/buzz/ に1投稿1ファイルで蓄積（_index.md / _counter.txt 自動生成）
  → AI抽出
  → knowledge/5_buzz/patterns.md（writerが最優先で読む勝ちパターン）
```

## モード

### add（バズ投稿を1件追加）
ユーザーが貼ったバズ投稿を `data/buzz/` に登録する。
本文に加えて、分かる範囲で以下のメタ情報を聞き取る／推定する:
- アカウント名（@〜）／媒体（threads / x）／URL
- 表示数・いいね・リプライ・リポスト
- ニッチ（例: AI事業、副業、スキンケア）
- メモ（なぜ伸びたかの一言所感）

登録は Python から行う:
```python
from threads_automation.buzz import BuzzLibrary, BuzzPost
lib = BuzzLibrary(data_dir="threads_automation/data")
lib.add(BuzzPost(text="...", account="@shiro_life0", source="x",
                 views=6083, likes=65, replies=1, niche="AI事業",
                 notes="Claude Codeで億事業。短文断言型"))
```
追加後、`_index.md` は自動で再生成される。

### import（旧データの取り込み）
`threads_automation/data/competitor_posts.json` を新構造へ移行する:
```bash
python -m threads_automation.buzz import
```

### analyze（勝ちパターンを抽出）
蓄積したバズ投稿を AI に分析させ、`knowledge/5_buzz/patterns.md` を更新する:
```bash
python -m threads_automation.buzz analyze
```
APIキー（ANTHROPIC_API_KEY / OPENAI_API_KEY）が必要。
キーが無い／オフライン時は、`data/buzz/` の全レコードを自分で読み、
analyze と同じ観点（共通要素／型／数字の使われ方／避けること）で
`knowledge/5_buzz/patterns.md` を手で書き起こしてもよい。

### list（一覧確認）
```bash
python -m threads_automation.buzz list
```

## 分析の観点（patterns.md に書くこと）
1. 伸びた投稿に共通する構造・1行目・テーマ・感情トリガー
2. 再現テンプレート化した「型」（1行目テンプレ＋構成）
3. 数字・固有名詞がフックでどう効いているか
4. このニッチで避けるべきスベりパターン

## 注意
- 生データ（`data/buzz/`）は手で書かない。必ず `add` / `import` 経由
- 抽出結果（`patterns.md`）は再収集→再分析で更新する複利資産
- 景表法NG表現の判定は `knowledge/07_ng-rules.md` を併用する
- 丸パクリ用ではない。「構造」を抽出して自分の投稿に転用するのが目的

## 引数
$ARGUMENTS — `add` / `import` / `analyze` / `list`。未指定時は現状（収集数・最終分析日）を報告。
