# 00 ナレッジ地図（INDEX）

> このプロジェクトのナレッジ全体の構造図。
> 「どこに何があるか」「どう育てるか」を最初に定義する。
> Claude Code はこの体系を読んでから各カテゴリを参照する。

## 思想：ナレッジ＝事業の心臓

> AIの精度は99%ナレッジで決まる（詳細は `3_strategy/14_business_model.md`）。
> プロンプト＝毎回ガチャ。ナレッジ＝毎回同じ質。
> センスを言語化してナレッジ化した瞬間、Claude Codeで無限にコピーできる。

このナレッジ体系は「投稿を作るマシン」の燃料。
回せば回すほど `5_buzz/` と `2_writing/06_references.md` に当たり型が溜まり、
出力精度が複利で上がっていく。**作って終わりではなく、毎回追記して分厚くする。**

## ディレクトリ構造

```
knowledge/
├── 00_index.md            ← このファイル（全体地図）
├── 07_ng-rules.md         ← 横断ルール（NG表現・景表法・ハッシュタグ禁止）※最優先で常時参照
│
├── 1_identity/            ── 誰が・誰に・どのジャンルで発信するか
│   ├── 01_profile.md          アカウントのペルソナ・キャラ設定
│   ├── 02_target.md           ターゲット読者の定義
│   └── 03_genre.md            発信ジャンルの範囲
│
├── 2_writing/             ── どう書くか（書き方の技術）
│   ├── 05_writing.md          書き方の黄金ルール・フック・タップ経済の構造
│   ├── 06_references.md       手で選んだバズ投稿の型（型1〜型7・具体例）
│   └── 16_buzz_templates.md   バズ投稿テンプレ集（調査ベース：フック穴埋め／拡散型／締め型）
│
├── 3_strategy/            ── どう売るか（戦略・収益・事業設計）
│   ├── 08_strategy.md         運用戦略
│   ├── 09_monetization.md     収益化の全体設計（Tier・価格帯）
│   ├── 13_launch_strategy.md  プロダクトローンチ（14日間＋note単体型）
│   ├── 14_business_model.md   事業の原則（集客×単価×成約率／リスト／ファネル）
│   └── 15_workflow.md         運用ワークフロー（需要の答え合わせ→テーマ→ナレッジ台本）
│
├── 4_domain/             ── 投稿ネタの源泉（専門知識）
│   ├── 04_domain.md           AIツール活用（ChatGPT/Claude/Gemini/Perplexity）
│   ├── 10_it_security.md      情報セキュリティ
│   ├── 11_ml_engineering.md   機械学習・エンジニアリング
│   └── 12_tech_trends.md      テック業界動向
│
└── 5_buzz/               ── バズ分析（自動収集→抽出。複利の中核）
    ├── _index.md             収集済みバズ投稿の一覧（自動生成）
    ├── patterns.md           収集データから抽出した最新の勝ちパターン（writer最優先）
    └── themes.md             今伸びるテーマ候補（需要の答え合わせ／buzz themes が生成）
```

## 各エージェントが読む場所

| エージェント | 主に読むカテゴリ |
|------------|----------------|
| `/writer` | `1_identity/` `2_writing/` `5_buzz/patterns.md` `07_ng-rules.md` |
| `/analyst` | 全カテゴリ＋ `data/insights_history.json` |
| `/researcher` | `5_buzz/` `data/buzz/` ＋ Web検索 |
| `/buzz` | `data/buzz/`（生データ）→ `5_buzz/patterns.md`（抽出先） |
| `/supervisor` | 全カテゴリ（不備チェック） |

## ナレッジを育てる複利サイクル（シロウ式）

```
① バズ投稿を収集          → data/buzz/ に蓄積（/buzz add）
② 勝ちパターンを抽出       → 5_buzz/patterns.md を更新（/buzz analyze）
③ writerが型を使って投稿    → 1_identity + 2_writing + 5_buzz を参照
④ 結果を分析             → analyst が当たり/外れを判定
⑤ 当たった型を追記         → 2_writing/06_references.md へ昇格
   （①へ戻る。回すほど精度が上がる資産になる）
```

## 更新ルール
- 新しい専門ネタ → `4_domain/` に番号付きで追加
- 新しい書き方の発見 → `2_writing/` に追加（シロウ式に「イントロの作り方」等で細分化してよい）
- バズの生データ → `data/buzz/`（手で書かない。`/buzz` 経由）
- 抽出した型 → `5_buzz/patterns.md`（`/buzz analyze` が自動更新）
