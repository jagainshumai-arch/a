# 12 IT業界・テック動向・開発ツール

> 情報系の大学生として、日常的に触れる技術・ツール・業界トレンドを投稿ネタに落とし込む。
> 「授業で習ったけど面白い」「バイト先で使った」「個人開発で試した」角度で語る。

## プログラミング言語トレンド（2025-2026）

### 言語別の現在地

| 言語 | 2026年の立ち位置 | 得意分野 |
|------|---------------|---------|
| **Python** | AI/ML の絶対王者、Web・スクリプト万能 | AI、データ、自動化 |
| **TypeScript** | Webフロント/サーバーのデファクト | Webアプリ、Node.js |
| **Rust** | システム・クラウドで急拡大 | OS、DB、CLI、Wasm |
| **Go** | クラウドネイティブの標準 | マイクロサービス、K8s |
| **Java** | 企業向けで依然強い | Android、バックエンド |
| **Kotlin** | Android公式、JVM系で人気 | モバイル |
| **Swift** | iOS/macOS専用 | Appleエコシステム |
| **C++** | ゲーム・組込・高性能 | UE5、ML基盤 |
| **Zig** | C++の次候補として注目 | システム |
| **Mojo** | Python互換+高速、AI特化 | ML研究（未成熟） |

### Pythonの最新動向
- **Python 3.13**（2024年10月）: 実験的 **フリースレッドモード**（GILなし）
- **Python 3.14**（2025年10月予定）: JITコンパイラ実装
- 実行速度は3.11から3.13で約15-30%向上
- `uv` がパッケージ管理の標準へ

### TypeScript / JavaScript動向
- **TypeScript 5.7+**: 型推論強化、ES2024対応
- **Bun**: Node.js代替、起動10倍速い
- **Deno 2.0**: Node.js互換性大幅改善
- **Vite**: ビルドツールのデファクト
- **React 19**: Server Components 安定化、`use` フック
- **Next.js 15**: Turbopack、Partial Prerendering
- **Svelte 5**: Runes API、最速フレームワーク争い
- **Astro**: コンテンツサイト特化、急成長

## Web開発の最新スタック

### フロントエンド選択肢
| フレームワーク | 特徴 | 使い所 |
|-------------|-----|-------|
| **React + Next.js** | 求人最多、エコシステム最強 | 大規模アプリ |
| **Vue + Nuxt** | 学習曲線穏やか、日本で人気 | 中規模 |
| **Svelte / SvelteKit** | コンパイラ型、最速 | 性能重視 |
| **Solid.js** | React風 + Signal、高速 | パフォーマンス |
| **Astro** | マルチフレームワーク、静的生成 | ブログ・ドキュメント |
| **Qwik** | Resumability、遅延ハイドレーション | 大規模EC |

### バックエンド選択肢
- **Node.js + Hono**: 軽量、エッジ対応
- **Python + FastAPI**: 型安全、自動ドキュメント生成
- **Python + Django**: 老舗、バッテリー込み
- **Rust + Actix/Axum**: 高性能
- **Go + Gin/Echo**: マイクロサービス王道
- **Ruby on Rails**: 2025年も健在（37signals）
- **Elixir + Phoenix**: リアルタイム特化

### データベース選択
| DB | 種類 | 使い所 |
|----|-----|-------|
| **PostgreSQL** | RDB | 万能、最強候補 |
| **MySQL** | RDB | Web定番 |
| **SQLite** | RDB | モバイル、組込、ローカル |
| **Turso / LibSQL** | 分散SQLite | エッジ対応 |
| **MongoDB** | NoSQL | 柔軟なスキーマ |
| **Redis / Valkey** | KVS | キャッシュ、セッション |
| **Firestore / Supabase** | BaaS | 個人開発 |
| **DuckDB** | 分析DB | データサイエンス |
| **ClickHouse** | 列指向 | ログ分析 |

## クラウド・インフラ

### 3大クラウドの日本シェア（2025年推定）
- **AWS**: 約50% - 老舗、サービス数最多
- **Microsoft Azure**: 約25% - 企業統合強い
- **Google Cloud**: 約15% - AI/ML特化で急伸
- その他（Oracle, IBM, さくら等）: 約10%

### サーバーレス / エッジ
- **Cloudflare Workers**: V8 Isolate、世界300都市配信
- **Vercel Edge Functions**: Next.jsとの統合
- **AWS Lambda**: 王道FaaS
- **Deno Deploy**: TypeScriptネイティブ
- **Fly.io**: Docker直デプロイ

### コンテナ / オーケストレーション
- **Docker**: 事実上の標準
- **Kubernetes (K8s)**: コンテナオーケストレーション王
- **Helm**: K8sパッケージ管理
- **ArgoCD**: GitOpsの定番
- **Istio / Linkerd**: サービスメッシュ

### Infrastructure as Code
- **Terraform / OpenTofu**: インフラのコード化標準
- **Pulumi**: TypeScript/Python でインフラ書ける
- **AWS CDK**: コード→CloudFormation
- **Ansible**: 構成管理

## DevOps / CI-CD

### 主要CI/CDツール
| ツール | 特徴 |
|-------|-----|
| **GitHub Actions** | GitHub統合、学生に最も身近 |
| **GitLab CI** | GitLab一体型 |
| **CircleCI** | 高速、オーケストレーション強い |
| **Jenkins** | 老舗、自由度高い |
| **Buildkite** | ハイブリッドランナー |

### オブザーバビリティ（監視）
- **Datadog**: 統合監視の王者
- **Grafana + Prometheus**: OSS王道
- **OpenTelemetry**: 標準規格として普及
- **Sentry**: エラー監視、学生は無料枠活用
- **Honeycomb**: 観測性特化

## オープンソース動向

### 注目プロジェクト（2025-2026）

#### AI/ML系
- **Hugging Face**: モデル・データセットのGitHub（30万+モデル）
- **LangChain / LangGraph**: LLMアプリ基盤
- **vLLM**: 高スループットLLM推論
- **Ollama**: ローカルLLM実行
- **LocalAI**: OpenAI API互換のセルフホスト
- **DeepSeek**: オープンソース推論モデル

#### 開発ツール
- **Zed**: Rust製の超高速エディタ（GitHub創業者の新作）
- **Cursor**: AI統合IDE
- **Bun**: Node.js代替ランタイム
- **Biome**: Prettier + ESLint を統合、Rust製で爆速

#### DB・データ
- **PGlite**: ブラウザで動くPostgres
- **DuckDB**: 分析用組込DB、Pythonで人気急上昇
- **Turso**: エッジSQLite
- **Valkey**: Redisのフォーク（ライセンス変更を受けて）

### ライセンス変更トレンド
- Elastic → AGPL + SSPL デュアル（2024年）
- Redis → SSPL + RSAL（2024年、Valkey誕生）
- HashiCorp → BSL（MPL→BSL、2023年、OpenTofu誕生）
- 「AGPLv3 / BSL / SSPL」がメガクラウド対策のデファクト化

## 情報系学生の常識ツール

### エディタ・IDE
- **VS Code**: 学生・実務ともに最多
- **Cursor**: VS CodeフォークのAI IDE、急拡大
- **JetBrains系** (IntelliJ, PyCharm等): 学生無料
- **Neovim / Vim**: ハッカー系の定番
- **Zed**: 新興、Rustで爆速

### ターミナル環境
- **WSL2** (Windows): Linux環境必須
- **iTerm2 / Warp / Ghostty**: モダンターミナル
- **zsh + oh-my-zsh / fish / nushell**: シェル
- **tmux / zellij**: セッション管理
- **starship**: プロンプトカスタマイズ

### 開発効率ツール
- **Git / GitHub**: バージョン管理の絶対前提
- **GitHub Copilot**: 学生無料（Education Pack）
- **Claude Code / Cursor**: AIペアプログラミング
- **Postman / Bruno / Hoppscotch**: API開発
- **Docker Desktop**: ローカル開発環境
- **ngrok**: ローカルサーバ公開

### 学生が無料で使える特典
- **GitHub Student Developer Pack**: 100+ツール無料
  - JetBrains全製品、AWS credits、DigitalOcean credits等
- **Notion + AI**: 学生無料
- **Figma**: 個人無料、教育プラン
- **Vercel**: 無料枠で個人サイト
- **Netlify / Cloudflare Pages**: 無料ホスティング
- **MongoDB Atlas**: 512MB無料
- **Supabase**: 無料枠充実

## 技術ニュースのソース（情報系学生の情報源）

### 英語系
- **Hacker News** (news.ycombinator.com): 朝イチで見る習慣を
- **Lobsters**: 厳選版HN
- **ArXiv**: AI論文プレプリント
- **The Register**: 硬派なITニュース
- **TechCrunch**: スタートアップ
- **InfoQ**: エンジニア向け技術記事
- **Changelog**: Podcast、幅広い技術

### 日本語系
- **はてなブックマーク テクノロジー**: 日本のHN
- **Qiita / Zenn**: 技術記事の2大プラットフォーム
- **ITmedia NEWS**: 硬派な日本IT
- **Publickey**: 公平な技術解説
- **日経クロステック**: 企業IT動向
- **gihyo.jp**: 技術評論社
- **InfoQ Japan**: 翻訳含む

### SNS / コミュニティ
- **X (旧Twitter)**: エンジニア界隈の情報源最強
- **Reddit**: r/programming, r/MachineLearning, r/LocalLLaMA
- **Discord**: Hugging Face, LangChain等の公式
- **Slack**: Kubernetes, Rustlangなど
- **Mastodon / Bluesky**: 技術系移住先
- **YouTube**: Fireship, Theo, ThePrimeagen, Yannic Kilcher

## 2025年に話題になった技術

### 注目キーワード
- **AIエージェント**: ChatGPT Agent, Claude Computer Use, Devin
- **MCPサーバー**: LLMとツールの標準接続
- **推論モデル**: o1, o3, R1, Gemini Thinking
- **Small Language Models (SLM)**: Phi-4, Gemma 3
- **Vibe Coding**: AIにコード書かせて動けばOK
- **Edge AI**: デバイス上でLLM実行
- **LLMガードレール**: Llama Guard, NeMo Guardrails

### 技術カンファレンス
- **AWS re:Invent**: 12月、ラスベガス
- **Google I/O**: 5月
- **WWDC**: 6月、Apple
- **Microsoft Build**: 5月
- **NeurIPS / ICML / ICLR**: AI研究3大会議
- **KubeCon**: CNCF主催
- **PyCon JP**: Python日本
- **RubyKaigi**: Ruby日本
- **Open Source Summit Japan**: Linux Foundation

## 日本のIT業界事情（情報系学生として知っておく）

### 就職市場（2026卒〜2027卒）
- **IT人材不足**: 2030年に45万人不足予測
- **SIer大手**: NTTデータ、NRI、富士通、NEC - 安定志向
- **Web系**: サイバーエージェント、リクルート、DeNA、メルカリ - 実力主義
- **外資系**: Google, Microsoft, AWS, Meta - 高年収
- **AIスタートアップ**: ELYZA, Stockmark, PKSHA, Preferred Networks

### 平均年収（新卒エンジニア、2025年目安）
- 大手SIer: 400-500万
- Web系大手: 500-700万
- 外資系: 700-1200万
- スタートアップ: 400-900万（幅広い）
- GAFAM: 800-1500万＋株（新卒）

### 資格は就活に効くか
- **基本情報技術者**: 情報系は取って当然扱い
- **応用情報技術者**: 2年生で取ると強い
- **AWS/Azure/GCPの資格**: 職種によっては必須
- **TOEIC**: 外資なら600以上欲しい
- **情報処理安全確保支援士**: セキュリティ職狙いの切り札
- **Kaggleメダル / GitHub Stars**: 資格より効く場合も

## 情報系大学生が語れる「硬派なテック豆知識」

- 「Python 3.13 で GIL が外せる。並列処理が真になる時代」
- 「Rust は C++ の後継として、K8s の多くが書き直されつつある」
- 「Bun は Node.js の10倍速い。起動時間が圧倒的」
- 「Cloudflare Workers は V8 Isolate で世界300都市に即配信」
- 「DuckDB はローカルPCで数GBのCSVをサクサク分析できる」
- 「GitHub Student Pack で JetBrains 全部無料。知らない学生が多すぎる」
- 「Hacker News を毎朝見る習慣が、3年後に差を生む」
- 「Zed エディタは Rust 製で、起動がVS Codeの5倍速い」
- 「OpenTofu は Terraform の OSS フォーク、HashiCorp のBSLライセンス変更から生まれた」
- 「LLM のコンテキスト 1M トークンは、本10冊分が一度に読める」
