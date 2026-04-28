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

## AI業界の資金調達・企業動向（2025-2026）

### ファンディングの爆発
- **Q1 2026**: AIスタートアップに **$1,780億（約27兆円）** が流入、2025年全体の**2倍**
- OpenAI・Anthropic・xAI・Waymoの4社で**全世界VCの65%**を吸収
- AI分野のメガラウンド（$10B+）が常態化

### 主要AI企業の評価額

| 企業 | 評価額（2026年4月） | 直近ラウンド | 累計調達額 |
|------|-------------------|------------|----------|
| **OpenAI** | $8,520億 | $1,220億（Series最新、2026年3月） | $1,500億+ |
| **Anthropic** | $3,800億（$8,000億+の提示を拒否中） | $300億 Series G（2026年2月） | $640億 |
| **xAI** | $2,300億 | $200億 Series E（2026年初） | $427億 |
| **Figure AI** | $390億 | $10億+ Series C（2025年9月） | $19億 |

### Anthropicの急成長
- 年間収益: 2025年1月の**$10億**→2026年4月の**$300億**（**30倍成長**）
- IPO検討中: Goldman Sachs, JPMorgan, Morgan Stanleyと協議、2026年10月上場の可能性
- 投稿切り口: 「Anthropicの売上が1年で30倍。AI企業の成長速度がバグってる」

### OpenAIの動向
- **Stargate計画**: SoftBankと共同の巨大データセンタープロジェクト（$400億融資）
- Microsoft: 累計$130億+投資、最大の戦略的投資家
- SoftBank: $300億 + $400億融資 = $700億のコミットメント

## スマートフォンAI / オンデバイスAI

### Apple + Google Gemini統合
- Apple Intelligence の基盤として**Gemini**を採用（年間約**$10億**の契約）
- Siri のフルリニューアルに Gemini Pro を活用
- iPhone 17 で本格デビュー予定
- 投稿切り口: 「AppleがSiriを捨ててGoogleのGeminiに乗り換えた話」

### Samsung Galaxy AI
- **Galaxy AIデバイス目標: 2026年末までに8億台**（2025年の4億台から倍増）
- Galaxy S26: **Gemini Nano 3**（100億パラメータ）をオンデバイスで実行
- Universal Screen Awareness: 画面上の情報をAIが理解、インターネット不要
- リアルタイム翻訳・プライバシーデータ処理をローカルで完結

### NPU（Neural Processing Unit）の進化
- Qualcomm Snapdragon 8 Elite: **80 TOPS**（兆回演算/秒）
- Apple A18 Pro: Neural Engine 強化
- Samsung Exynos 2500: オンデバイスLLM対応
- 投稿切り口: 「スマホの中にAI専用チップが入ってる時代。パソコンいらなくなるかも」

## ノーコード / ローコードAIツール

### 主要プラットフォーム比較

| ツール | 特徴 | GitHub Stars | 価格帯 |
|-------|------|------------|-------|
| **Dify** | AIアプリ統合開発。RAG・ワークフロー・監視を一体化 | **90,000+** | 無料〜$159/mo |
| **n8n** | ワークフロー自動化。70+ AIノード + LangChain統合 | 50,000+ | 自己ホスト: $5-20/mo |
| **Flowise** | チャットボット開発特化。LangChain基盤 | 35,000+ | OSS無料 |
| **Langflow** | RAGパイプライン特化。ビジュアルビルダー | 40,000+ | OSS無料 |
| **Make** | ビジュアル自動化。AI連携豊富 | N/A | $90-180/mo |
| **Zapier** | 最大の連携数。AI Agents対応 | N/A | $1,200-1,500/mo |

### n8n 2.0（2025年12月リリース）
- エンタープライズ級セキュリティ（分離コード実行、RBAC）
- **12,000レコード/分**の処理性能
- LangChain統合で70+ AIノード
- 投稿切り口: 「n8nなら月$5でZapierの$1,500と同じことができる」

### Zapier AI（2025-2026）
- **AI Agents** 機能（2025年10月追加）
- Zapier Copilot: AIがワークフローを自動構築
- **MCP（Model Context Protocol）** 対応を2026年に予定

## AI × 教育

### Khanmigo（Khan Academy）
- GPT-4ベースのソクラテス式AIチューター
- 2024-25年度: **40,000人→700,000人**の K-12学生が利用（17.5倍成長）
- 2025-26年度: **100万人突破**の見通し
- Google との積極的パートナーシップ

### Duolingo Max
- AI搭載のロールプレイ会話練習
- 回答の詳細解説をAIが自動生成
- 学生向け投稿切り口: 「Duolingo Max で英会話の練習相手がAIになった」

### Google NotebookLM 2.0
- アップロードした教材から**自動でフラッシュカード・クイズを生成**
- ノート・教科書・PDFを読み込ませるだけ
- 投稿切り口: 「NotebookLMに教科書読ませたら自動で期末テスト対策が完成した」

### AI教育市場
- 2025年: **$58.8億** → 2030年: **$322.7億** 予測（CAGR 40%+）

## SaaS × AI統合（2025-2026）

### Microsoft 365 Copilot
- **企業向け**: $30/ユーザー/月
- **個人向け Copilot Pro**: $20/月
- **Microsoft 365 Premium**: $19.99/月（Office + Copilot バンドル）
- 2026年7月: パッケージ刷新 + 値上げ（AI + セキュリティ機能統合）
- 投稿切り口: 「Microsoft がOfficeにAI入れて値上げ。でもこれ使うと生産性3倍」

### Notion AI
- 2026年初: **Business / Enterprise プランにAI標準バンドル**
- **Notion 3.3**（2026年2月）: **Custom Agents** 追加（チーム専用AIワークフロー）
- ワークスペース横断Q&A、AI搭載データベース、接続検索
- 新規ユーザーはBusiness（$15/月）以上でAI利用可能

### Adobe Firefly
- **Firefly AI Assistant**（2026年4月）: Creative Cloud全体で複数ステップのワークフローを自動実行
- AI動画エディタ + **Kling 3.0** モデル統合
- パートナーモデル: Google, OpenAI, Runway, Luma AI, ElevenLabs, Topaz Labs
- **$10/月で無制限AI画像生成**
- 投稿切り口: 「Adobe FireflyがAI動画編集対応。月$10でプロ級コンテンツ作れる」

### Canva
- **Canva Pro**: 約**$130/年**
- Magic Studio: テキスト→デザイン自動生成
- AI搭載のプレゼン・動画・SNS画像作成

## 自動運転 / ロボティクス

### Waymo（Alphabet傘下）
- **週50万回の有料乗車**（2026年3月時点）、2024年5月の**10倍**
- **10都市で商用サービス**: Phoenix, SF, LA, Austin, Atlanta, Miami, Dallas, Houston, San Antonio, Orlando
- 2026年内にさらに追加予定: Denver, Detroit, Las Vegas, Nashville, San Diego, DC, **ロンドン**
- NYC と**東京**でテスト走行中
- **3,000台のロボタクシー**が稼働中
- 2026年末目標: **週100万回の乗車**
- 投稿切り口: 「Waymoが週50万回走ってる。東京でもテスト始まった」

### Tesla Optimus（ヒューマノイドロボット）
- **Gen 3**: 2026年2月からFremont工場で生産開始
- Fremont ライン: **年間100万台**の生産能力
- Gigafactory Texas: **年間1,000万台**の生産ライン準備中（2027年〜）
- xAI の **Grok LLM** を統合（会話AI）
- 消費者向け販売: 2027年末予定、目標価格 **$20,000-30,000**
- FSD v15: 2026年末〜2027年初にリリース予定

### Figure AI
- **$390億評価額**（2025年9月 Series C、$10億+調達）
- 累計調達: **$19億**
- Figure 02: 食洗機・洗濯機の操作を自律で実行
- Figure 03: 2025年10月発表、汎用ロボットへの進化
- 投稿切り口: 「Figure AIのロボットが食洗機を自分で操作してる動画がやばい」

## エッジコンピューティング / IoT AI

### 市場規模
- **Edge AI市場**: 2025年 $249億 → 2026年 $300億 → 2034年 $1,431億
- **Edge Computing市場**: 2025年 $214億 → 2035年 $6,092億（CAGR 28%）

### IoTデバイス
- 2026年の**エッジ対応IoTデバイス**: 世界で**58億台**（前年比13%増）
- 新規IoTデバイスの **70%がAIチップ搭載**（Intel / Qualcomm製）

### 企業導入
- 米国CIOの **97%** が2025-2026年のロードマップにEdge AIを組み込み
- **90%の企業**がEdge AI予算を増額
- 投稿切り口: 「スマホもIoTもエッジAI。クラウドに送らず手元で処理する時代」

## ブロックチェーン / Web3 × AI

### Web3 AIエージェント
- **$43億市場、282以上のプロジェクト**が資金調達済み（2025年）
- AIエージェントがウォレットを保有し、スマートコントラクトと自律的にやり取り
- DeFiが手動トレードから**インテントベースの自動実行**へ

### 分散コンピューティング
- **DePINプロトコル**: Render, Akash がAI訓練/推論のセカンダリ市場を確立
- クラウドの代替として、コスト効率の高い分散GPU提供

### ユースケース
- 自律エージェントによるDeFiトレーディング
- 暗号技術ベースのデータマーケットプレイス
- ハイブリッドスタック: クラウドで訓練 + ブロックチェーンで検証・決済

## デジタルノマド / リモートワーク

### 日本のデジタルノマドビザ（2024年3月開始）
- 滞在期間: **6ヶ月**
- 年収要件: **1,000万円以上**（約$66,864）
- 健康保険: 1,000万円以上の補償が必須
- 日本国外の雇用主/事業からの収入であること
- 家族帯同可能（追加収入証明不要）

### グローバル統計
- デジタルノマド人口: **4,000万人以上**（2025年、2020年から**60%増**）
- 日本・韓国: ノマド到着数の前年比成長率が最速
- 内訳: **66%がフルタイムリモート社員**、34%がフリーランス/事業主

### 東京のコワーキング
- Impact HUB Tokyo、Hive Shibuya、The Company Osaka
- SIMプラン: IIJmio / 楽天モバイル で5-20GB **月額2,000-4,000円**
- 投稿切り口: 「日本のノマドビザ、年収1,000万円必要。AIで仕組み作ればいける」

## 2025-2026年に話題になった技術

### 注目キーワード
- **AIエージェント**: ChatGPT Agent, Claude Computer Use, Devin
- **MCPサーバー**: LLMとツールの標準接続
- **推論モデル**: o1, o3, R1, Gemini Thinking
- **Small Language Models (SLM)**: Phi-4, Gemma 3
- **Vibe Coding**: AIにコード書かせて動けばOK
- **Edge AI**: デバイス上でLLM実行
- **LLMガードレール**: Llama Guard, NeMo Guardrails
- **Agentic AI**: 自律的に判断・行動するAI
- **オンデバイスAI**: NPU搭載スマホ・PC
- **Web3 × AI**: ブロックチェーン上のAIエージェント

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

## 日本のAIスタートアップ（2025-2026）

### 主要企業

| 企業 | 評価額 / 動向 | 特徴 |
|------|-------------|------|
| **Sakana AI**（東京） | $3億以上の資金調達 | 元Google研究者が創業。進化的アルゴリズムでAIモデル生成 |
| **Preferred Networks (PFN)** | 評価額 $20億以上 | 深層学習の老舗。MN-Core チップ独自開発 |
| **ELYZA** | KDDIが買収 | 日本語LLM特化。大企業向けカスタムLLM |
| **Stockmark** | - | 企業向けAIテキスト分析 |
| **PKSHA Technology** | 東証グロース上場 | 自然言語処理・対話AI |
| **ABEJA** | 東証グロース上場 | デジタルプラットフォーム事業 |

### 日本のAI市場
- 企業の生成AI導入率: **30-50%**（大企業は50%超）
- 個人利用率: **20-35%**（米国40-50%と比べ低い）
- さくらインターネット: ソブリンクラウドとして**1,000億円以上**のデータセンター投資
- 投稿切り口: 「Sakana AIって知ってる？元Google研究者が東京で作ったAI会社が$3億調達」

## 日本のIT業界事情（情報系学生として知っておく）

### IT人材市場（最新）
- **IT人材不足**: 2030年に **79万人不足** 予測（上方修正）
- IT系求人倍率: **5倍以上**（他業種平均の約3倍）
- AI/ML エンジニアの需要が特に急拡大
- 投稿切り口: 「IT人材不足79万人。プログラミングできる大学生は引く手あまた」

### 就職市場（2026卒〜2027卒）
- **SIer大手**: NTTデータ、NRI、富士通、NEC - 安定志向
- **Web系**: サイバーエージェント、リクルート、DeNA、メルカリ - 実力主義
- **外資系**: Google, Microsoft, AWS, Meta - 高年収
- **AIスタートアップ**: Sakana AI, ELYZA, Stockmark, PKSHA, Preferred Networks

### 平均年収（新卒エンジニア、2025-2026年目安）
- 大手SIer: 400-500万
- Web系大手: 500-700万
- 外資系: 700-1200万
- スタートアップ: 400-900万（幅広い）
- GAFAM: 800-1500万＋株（新卒）

### 資格は就活に効くか
- **基本情報技術者（FE）**: 情報系は取って当然（CBT化で合格率40-50%に上昇）
- **応用情報技術者（AP）**: 2年生で取ると強い（合格率22-25%）
- **AWS/Azure/GCPの資格**: 職種によっては必須
- **TOEIC**: 外資なら600以上欲しい
- **情報処理安全確保支援士**: セキュリティ職狙いの切り札
- **Kaggleメダル / GitHub Stars**: 資格より効く場合も

## 日本のデジタル政策（2025-2026）

### デジタル庁
- **ガバメントクラウド**: AWS / Azure / GCP / Oracle / さくらインターネット
- マイナンバーカード普及率: **70-80%**
- マイナ免許証: 2025年3月開始

### プログラミング教育
- **情報I**: 2025年1月共通テストで初実施
- **数理・データサイエンス・AI教育**: 200以上の認定プログラム
- 高校「情報II」: データサイエンス・AI基礎を含む
- 投稿切り口: 「共通テストに"情報"が入った。プログラミングが受験科目の時代」

### クラウド市場（日本）
- AWS: 約50% → Azure: 約25% → GCP: 約15% → その他10%
- **さくらインターネット**: 国産ソブリンクラウドとして政府案件獲得
- 1,000億円以上のデータセンター投資（北海道石狩等）

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
- 「OpenAIの評価額$8,520億。日本のGDP（$4.2兆）の2割に匹敵する1社」
- 「Anthropicの売上が1年で30倍。AI企業の成長がバグってる」
- 「Samsung Galaxy S26のAIチップ、100億パラメータのLLMをオフラインで動かす」
- 「Waymoのロボタクシー、週50万回走行。2026年末には100万回の予定」
- 「Figure AIのロボットが$390億の評価。食洗機を自分で操作する」
- 「Difyは90,000 GitHub Stars。ノーコードでAIアプリが作れる」
- 「n8nなら月$5でZapierの$1,500相当の自動化ができる」
- 「NotebookLMに教科書読ませたら期末テスト対策が10分で完成した」
- 「共通テストに"情報"が入った。プログラミングが受験科目の時代」
- 「IT人材2030年に79万人不足。今プログラミングやってる学生は超有利」
- 「Web3のAIエージェントが自分でウォレット持って取引する時代」
- 「日本のノマドビザ、年収1,000万必要。AIで仕組み作ればワンチャンいける」
