# Threads × AI 自動収益化パイプライン

Threads投稿のリサーチ→分析→作成→投稿→結果取得→監視を完全自動化するシステム。

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Supervisor（監視）                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Researcher│→│ Composer  │→│Publisher │→│ Fetcher  │ │
│  │(リサーチ) │  │(投稿作成) │  │(投稿公開) │  │(結果取得) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │             │             │       │
│  ┌────▼─────────────▼─────┐ ┌────▼─────────────▼─────┐ │
│  │      AI Client         │ │   Threads API Client   │ │
│  │  (OpenAI / Anthropic)  │ │  (graph.threads.net)   │ │
│  └────────────────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## パイプライン（1サイクル）

| Step | モジュール | 処理内容 |
|------|-----------|---------|
| 1 | Fetcher | 直近投稿のインサイト（views/likes/replies）を取得 |
| 2 | Fetcher | 高パフォーマンス/低パフォーマンス投稿を分類 |
| 3 | Composer | 低パフォーマンス投稿をAI分析→リライト→再投稿 |
| 4 | Researcher → Composer → Publisher | リサーチ→新規投稿作成→公開 |
| 5 | Supervisor | レポート生成・ログ出力 |

## セットアップ

### 1. 環境変数を設定

```bash
cp threads_automation/.env.example .env
# .env を編集してAPIキーを設定
```

### 2. Threads APIトークンの取得

1. [Meta for Developers](https://developers.facebook.com/) でアプリを作成
2. Threads用のOAuth認証を設定
3. 必要なスコープ: `threads_basic`, `threads_content_publish`, `threads_manage_insights`
4. 長期トークン（60日有効）を取得

### 3. 実行

```bash
# フルパイプライン（1サイクル）
python -m threads_automation.pipeline \
  --niche "美肌・スキンケア" \
  --target "育児中の30代ママ" \
  --cycles 1

# リサーチのみ
python -m threads_automation.pipeline \
  --niche "副業・AI活用" \
  --target "副業初心者の会社員" \
  --mode research

# 投稿の下書き生成のみ（投稿はしない）
python -m threads_automation.pipeline \
  --niche "副業・AI活用" \
  --target "副業初心者の会社員" \
  --mode compose

# インサイト取得のみ
python -m threads_automation.pipeline --niche any --target any --mode fetch

# パフォーマンスレポート
python -m threads_automation.pipeline --niche any --target any --mode report

# 無限ループ（60分ごとに自動実行）
python -m threads_automation.pipeline \
  --niche "美肌・スキンケア" \
  --target "育児中の30代ママ" \
  --cycles 0
```

## 全自動投稿アプリ（autopost.py）

人の承認を挟まず「生成 → 安全チェック → 本文＋リプ欄を自動投稿」まで一気に回す
スタンドアロンアプリ（リポジトリ直下 `autopost.py`）。

```bash
python autopost.py --now              # 今すぐ1本 生成して投稿
python autopost.py --count 3 --now    # 今すぐ3本（5分間隔で）投稿
python autopost.py --loop             # 朝/昼/夜の最適時間帯に自動投稿し続ける
python autopost.py --now --dry-run    # 投稿せず生成結果だけ確認（API必要）
python autopost.py --sample --dry-run # APIなしでパイプライン動作確認
```

**安全装置（全自動でも事故らないための仕組み）:**
- 景表法NG表現の自動検出（「確実に稼げる」等を検出したら投稿せず再生成）
- ハッシュタグの自動除去（Threadsでは逆効果のため）
- 直近20件との重複チェック（同じ1行目を連投しない）
- 1日の投稿上限（デフォルト3本）と最適時間帯スケジューリング
- 本文＋リプ欄（セルフリプライ）でタップ経済構造を自動構築

Webダッシュボード（`app.py`）の「⚡ 全自動で1本投稿」ボタンからも同じ処理を実行できる。

### 投稿コンソール Web UI（webapp.py）

`autopost.py` の機能をブラウザの見やすいUIから操作できるアプリ。
**Flask等のインストール不要**（Python標準ライブラリの `http.server` のみ）。

```bash
python webapp.py            # http://127.0.0.1:8000 で起動
python webapp.py --open     # 起動後にブラウザを自動で開く
python webapp.py --port 5000
```

- 「🎲 生成してプレビュー」: 投稿せず本文＋リプ欄を生成し、安全チェック結果・文字数を表示
- 「🚀 この内容でThreadsに投稿」: プレビューした内容を本文＋セルフリプライで投稿
- 「🧪 サンプル生成」: APIを使わずUIの動作確認
- 「📝 下書き」: 作り置きした下書きを確認し、1本ずつ投稿・削除
- ステータス（API接続・投稿時間帯・本日の投稿数・残り枠）と投稿履歴を一覧表示

### 毎朝の下書きまとめ生成（--drafts / 毎朝9時）

投稿はせず、レビュー用の下書きだけをまとめて作る機能。

```bash
python autopost.py --drafts 5   # 下書きを5本 生成して保存（投稿しない）
```

- 保存先: `data/drafts.json`（webappの「下書き」に表示）＋ `data/drafts/YYYY-MM-DD.md`（スマホ等で読む用）
- 生成時に景表法NG・ハッシュタグ・重複チェック済み。1行目が既存下書き/投稿と被らないよう調整
- webapp の「下書き」欄から中身を確認し、良いものだけ「🚀 これを投稿」で公開できる

**毎朝9時に自動で5本作る（Windows）:**

`setup_schedule.bat` をダブルクリックするだけで、毎朝9時に下書き5本を自動生成する
予約（タスクスケジューラの `ThreadsMorningDrafts`）が登録される。※PCが起動している必要あり。

```bat
setup_schedule.bat        :: 毎朝9時の予約を登録（1回だけ実行）
```

予約を止めるとき: `schtasks /Delete /TN "ThreadsMorningDrafts" /F`

**タスクスケジューラ手動設定（バッチが使えない場合）:**
1. 「タスクスケジューラ」を開く →「基本タスクの作成」
2. トリガー: 毎日 / 開始 09:00
3. 操作: プログラムの開始 → `morning_drafts.bat` を選択
4. 完了。「スリープ解除して実行」「見逃したら起動時に実行」はプロパティで調整可

### Typefully 連携（クラウド予約投稿・PCオフでもOK）

生成した投稿を Typefully に「予約下書き」として送り、クラウド側で予約時刻に
自動投稿する。自分のPCが起動していなくても投稿されるのが利点（タスクスケジューラの
「PCが起動している必要」を回避できる）。Typefully API v2 を使用。

**準備:**
1. Typefully（有料プラン）で Threads アカウントを連携
2. Settings → API で APIキーを取得
3. `.env` に `TYPEFULLY_API_KEY=...` を追加

```bash
python typefully.py --check     # 接続確認＆投稿先(social set)一覧
python typefully.py --sample    # サンプルを次の空き枠に予約
python typefully.py --drafts    # data/drafts.json の下書きを全部 予約送信
python typefully.py --drafts --at 2026-07-11T09:00:00Z  # 時刻指定で予約
```

`--at` は `next-free-slot`（既定・Typefullyの次の空きスロット）/ `now`（即時）/ ISO日時。
本文＋リプ欄はスレッド（本文→セルフリプライ）として送られる。

webapp（`python webapp.py`）でも、プレビューや各下書きの「🗓 Typefullyで予約」
ボタンから同じ予約ができる。

**投稿時間帯・本数の調整（ソース改変不要・`.env`で設定）:**

```bash
POST_SLOTS=07:30,12:15,20:30   # --loop が投稿する時間帯（本数はこの個数に連動）
DAILY_LIMIT=3                  # 1日の最大投稿本数（安全上限）
POST_INTERVAL_SEC=300          # --count 連投時の投稿間隔（秒）
```

例: 1日4本にしたいなら `POST_SLOTS=07:30,12:15,18:00,21:00` と `DAILY_LIMIT=4` を `.env` に記載。
起動時バナーに反映後の時間帯と上限が表示されるので確認できる。常駐運用は `python autopost.py --loop`。

## バズ収集・分析（buzz.py / /buzz）

伸びた投稿を蓄積し、勝ちパターンを抽出してナレッジに反映する複利サイクル。

```bash
python -m threads_automation.buzz import   # competitor_posts.json を取り込む
python -m threads_automation.buzz list     # 蓄積済みバズ投稿を一覧
python -m threads_automation.buzz analyze  # 勝ちパターンを抽出 → knowledge/5_buzz/patterns.md
```

生データは `data/buzz/`（1投稿1ファイル＋`_index.md`自動生成）、
抽出した型は `knowledge/5_buzz/patterns.md`（writerが最優先で参照）。

## 競合データの手動追加

Threads APIでは他者の投稿を検索できないため、手動でデータを追加:

```bash
# data/competitor_posts.json に以下の形式で追加
[
  {
    "text": "投稿テキスト",
    "source": "threads",
    "estimated_views": 15000,
    "estimated_likes": 320,
    "niche": "ニッチ名",
    "notes": "メモ"
  }
]
```

## ファイル構成

```
threads_automation/
├── __init__.py
├── config.py          # 設定管理
├── ai_client.py       # AI API（OpenAI/Anthropic）統一クライアント
├── threads_api.py     # Threads Graph API クライアント
├── researcher.py      # リサーチ・分析エンジン
├── composer.py        # AI投稿作成エンジン
├── publisher.py       # 投稿公開・履歴管理
├── fetcher.py         # インサイト取得・蓄積
├── supervisor.py      # パイプライン全体の自動監視
├── pipeline.py        # CLIエントリポイント
├── .env.example       # 環境変数テンプレート
├── README.md
└── data/
    ├── competitor_posts.json    # 競合投稿データ（手動収集）
    ├── publish_history.json     # 投稿履歴（自動生成）
    ├── insights_history.json    # インサイト履歴（自動生成）
    └── reports/                 # サイクルレポート（自動生成）
```

## 環境変数一覧

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `THREADS_ACCESS_TOKEN` | ○ | Threads APIアクセストークン |
| `THREADS_USER_ID` | ○ | ThreadsユーザーID |
| `OPENAI_API_KEY` | △ | OpenAI APIキー（どちらか必須） |
| `ANTHROPIC_API_KEY` | △ | Anthropic APIキー（どちらか必須） |
| `AI_MODEL` | × | 使用モデル（デフォルト: gpt-4o） |
| `SUPERVISOR_INTERVAL` | × | 監視間隔・分（デフォルト: 60） |
| `DATA_DIR` | × | データ保存先（デフォルト: data） |
