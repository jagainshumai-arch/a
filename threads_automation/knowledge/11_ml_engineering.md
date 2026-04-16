# 11 機械学習・AIエンジニアリング専門知識

> 情報系の大学生として、研究室・競プロ・Kaggle・個人開発で使える硬派なAIナレッジ。
> 「使ったことある人だけが語れる」具体性を重視。

## LLM（大規模言語モデル）の基礎知識

### 主要モデルのスペック（2025-2026）

| モデル | 提供元 | 特徴 | コンテキスト |
|-------|-------|------|-------------|
| **Claude Opus 4.6** | Anthropic | 日本語最強クラス、推論モデル | 200K |
| **Claude Sonnet 4.6** | Anthropic | コスパ最強、Claude Code搭載 | 200K |
| **GPT-5 / GPT-4o** | OpenAI | マルチモーダル、o1系は推論特化 | 128K |
| **Gemini 2.5 Pro** | Google | 圧倒的長文、Google連携 | **1M〜2M** |
| **Llama 4 Scout** | Meta | オープンソース、MoE 17B active | **10M** |
| **Llama 4 Maverick** | Meta | 400B MoE、17B active | 1M |
| **DeepSeek-R1** | DeepSeek | オープンソース推論モデル | 128K |
| **Mistral Large 2** | Mistral | EU発、商用可 | 128K |
| **Qwen 2.5** | Alibaba | 0.5B〜72B、コーディング強い | 128K |
| **Phi-4** | Microsoft | 14Bで大モデル級性能 | 16K |
| **Gemma 3** | Google | 1B/4B/12B/27B、Vision対応 | 128K |

### LLMの内部構造（学部生なら理解しておきたい）
- **Transformer**: Attention Is All You Need（2017年）が原点
- **Self-Attention**: クエリ(Q)・キー(K)・バリュー(V)の3行列で相関を計算
- **Multi-Head Attention**: 複数の注意機構を並列化
- **FFN**: Feed-Forward Network、各トークンを独立処理
- **Positional Encoding**: 位置情報を埋め込み（RoPEが主流に）
- **MoE（Mixture of Experts）**: 部分的な専門家のみ活性化、計算コスト削減
- **トークナイザー**: BPE (Byte-Pair Encoding)、tiktoken、SentencePiece

### 数字で押さえる事実
- GPT-3: 175Bパラメータ、訓練コスト約460万ドル
- GPT-4: 推定1.76Tパラメータ（MoE構成）
- Llama 3.1 405B: 訓練に**3,930万GPU時間**（H100換算）
- DeepSeek-V3: **訓練コスト557万ドル**で671B MoEを完成（業界に衝撃）
- Claude 3.5 Sonnet: **1Mトークン=約3ドル**の入出力コスト

## プロンプトエンジニアリング（高度編）

### 基本7技法
1. **Zero-shot**: 例なしで指示だけ
2. **Few-shot**: 3〜5個の例を見せてから本題
3. **Chain-of-Thought (CoT)**: 「ステップバイステップで考えて」
4. **Self-Consistency**: 複数回生成→多数決（数学問題で5-15%精度UP）
5. **Tree-of-Thought (ToT)**: 思考を枝分かれさせて評価
6. **ReAct**: Reasoning + Acting、ツール使用エージェントの基礎
7. **Constitutional AI**: 自己批判→自己修正

### Claude専用テクニック
- **XMLタグ構造化**: `<context>` `<task>` `<format>` で精度激変
- **Prefill（前置詞）**: アシスタント応答の冒頭を固定
- **Extended Thinking**: `<thinking>` タグで内部思考を引き出す
- **Prompt Caching**: 長いシステムプロンプトをキャッシュ→**コスト90%削減**

### プロンプトの数値効果（研究ベース）
- 「Let's think step by step」を付けるだけで **GSM8K で17.7% → 78.7%**
- Few-shot（8例）で **MMLU で +7%**
- Self-Consistency (n=40) で **推論タスクで +18%**
- Contextual Retrieval（Anthropic, 2024年9月）: 検索性能 **+49%**

## AIエージェント・フレームワーク

### 主要フレームワーク比較

| フレームワーク | 提供元 | 特徴 | 用途 |
|-------------|-------|------|------|
| **LangChain / LangGraph** | LangChain | グラフベース、750+統合 | 汎用LLMアプリ |
| **LlamaIndex** | LlamaIndex | RAG特化、Workflow Engine | ドキュメントQA |
| **CrewAI** | CrewAI | 役割ベース、マルチエージェント | チーム型タスク |
| **AutoGen** | Microsoft | イベント駆動、会話型 | 研究・実験 |
| **Claude Agent SDK** | Anthropic | Claude Code基盤 | ターミナル統合 |
| **OpenAI Agents SDK** | OpenAI | 2025年3月公開、ハンドオフ対応 | 本番エージェント |
| **Semantic Kernel** | Microsoft | C#/Python対応 | 企業向け |
| **Haystack** | deepset | NLP特化 | 検索系 |

### エージェントの設計パターン
- **ReAct**: 考える→行動→観察→繰り返す
- **Plan-and-Execute**: 計画→実行（LangGraph の王道）
- **Multi-Agent**: 複数エージェントが協調（CrewAI）
- **Reflection**: 自己批評→改善
- **Tool Use**: Function Calling / MCP でツール実行

### MCP（Model Context Protocol）
- Anthropicが2024年11月に公開したオープン規格
- 「LLMとツール/データの接続を標準化するUSB-C」
- Claude Desktop、Claude Code、Cursor等が対応
- サーバー側を1回書けば、どのクライアントからも使える
- 2025年時点で **数千のMCPサーバーが公開**

## RAG（Retrieval-Augmented Generation）

### RAGの基本フロー
1. ドキュメントを **チャンク化**（小さく分割）
2. Embedding モデルで **ベクトル化**
3. **ベクターDB** に保存
4. クエリもベクトル化→類似検索
5. 検索結果をプロンプトに埋め込んで生成

### チャンキング戦略
| 手法 | 説明 | 用途 |
|------|------|-----|
| **Fixed-size** | 512-1024トークンで固定分割 | 汎用 |
| **Recursive** | 段落→文→トークンの順で分割 | Markdown/PDF |
| **Semantic** | 意味の切れ目で分割（埋め込み類似度） | 高精度RAG |
| **Document-structure** | 見出し・コード・表を認識 | 技術文書 |
| **Late Chunking** | 全文埋め込み→後で分割（Jina, 2024） | 文脈保持 |

### ベクターDB比較

| DB | 特徴 | 無料枠 | 適した用途 |
|----|------|-------|----------|
| **Chroma** | Python埋め込み、最も簡単 | ローカル無制限 | 個人プロジェクト |
| **FAISS** | Facebook製、超高速 | ローカル無制限 | 研究・プロトタイプ |
| **Pinecone** | マネージド、サーバーレス | 1 index, 100K vectors | 本番稼働 |
| **Weaviate** | OSS、ハイブリッド検索内蔵 | セルフホスト | 本格RAG |
| **Qdrant** | Rust製、超高速 | セルフホスト | 高負荷用 |
| **pgvector** | PostgreSQL拡張 | DB次第 | 既存PG資産活用 |

### Advanced RAG テクニック
- **Hybrid Search**: BM25（キーワード）+ ベクトル検索の組み合わせ
- **Re-ranking**: Cohere Rerank / Cross-Encoder で順位を再計算
- **HyDE**: 仮想回答を生成→その埋め込みで検索
- **Query Decomposition**: 複雑な質問を分解
- **Parent-Document Retrieval**: 小チャンクで検索、親文書を返す
- **Contextual Retrieval**: Anthropic方式、チャンク前に文脈要約を付加
- **GraphRAG**: Microsoft方式、知識グラフで関係性を捉える

## ローカルLLM実行

### Ollama（一番簡単）
```bash
# インストール
curl -fsSL https://ollama.com/install.sh | sh

# モデル実行
ollama run llama3.1:8b       # 8Bモデル
ollama run qwen2.5:14b       # コーディング強い
ollama run gemma3:12b        # Google製
ollama run deepseek-r1:14b   # 推論モデル

# APIサーバー
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "こんにちは"
}'
```

### 量子化とVRAM要件

| モデルサイズ | Q4_K_M (GGUF) | Q8 | FP16 |
|------------|--------------|-----|------|
| 7-8B | 約4.5GB | 約8GB | 約16GB |
| 13-14B | 約8GB | 約14GB | 約28GB |
| 30-34B | 約20GB | 約35GB | 約68GB |
| 70B | 約40GB | 約70GB | 約140GB |

### 量子化形式の使い分け
- **GGUF**: llama.cpp/Ollama用、CPU+GPU両対応、一番普及
- **GPTQ**: GPU専用、品質バランス
- **AWQ**: GPU専用、推論が一番速い
- **EXL2**: ExLlamaV2、VRAM最適化の鬼

### 一般的な学生PCで動くモデル目安
- RAM 16GB（GPU無し）: 7B Q4（遅い）
- RTX 3060 12GB: 13B Q4 で快適
- RTX 4070 Ti 12GB: 14B Q4 高速 / 34B Q4 ギリギリ
- RTX 4090 24GB: 34B Q4 高速 / 70B Q2 何とか
- Apple M2/M3 Pro 32GB: 13B〜34B まで（Unified Memory強い）

## Python でAI開発

### 環境構築（2025年のベストプラクティス）
- **uv**（Astral製、Rust実装）: **pipの10-100倍高速**。デファクト化進行中
- poetry, rye, pipenv は **uv に吸収されつつある**
- conda は AI/ML 界隈では下火（CUDA依存のみ）

```bash
# uv インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクト作成
uv init my-ai-project
cd my-ai-project
uv add torch transformers datasets peft accelerate
uv run python main.py
```

### 必携ライブラリ（2025年）

| カテゴリ | ライブラリ | 特徴 |
|---------|----------|------|
| **DL基盤** | PyTorch 2.6 | torch.compile成熟、FlexAttention |
| **LLM** | Transformers 4.48+ | 30万+モデル、HF Hub連携 |
| **LoRA** | PEFT | 1-2%パラメータで微調整 |
| **RLHF** | TRL | SFTTrainer, DPOTrainer |
| **量子化** | bitsandbytes | 8bit/4bit on-the-fly |
| **推論最適化** | vLLM | PagedAttention、最高スループット |
| **データ処理** | Polars | Pandasより5-50倍速い |
| **MLOps** | MLflow, W&B | 実験管理、モデルレジストリ |
| **可視化** | Plotly, seaborn | 論文向けmatplotlib |
| **型検証** | Pydantic v2 | Rust実装、高速 |

### ファインチューニング（LoRA実装例）
```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B")

config = LoraConfig(
    r=16,                    # ランク
    lora_alpha=32,           # スケーリング
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, config)
model.print_trainable_parameters()
# trainable params: 6.8M || all params: 8.0B || trainable%: 0.085
```

### API料金比較（2026年4月時点の目安、1Mトークンあたり）

| モデル | 入力 | 出力 | 備考 |
|-------|-----|-----|------|
| **Claude Opus 4.6** | $15 | $75 | 最高品質 |
| **Claude Sonnet 4.6** | $3 | $15 | コスパ最強 |
| **Claude Haiku 4.5** | $0.80 | $4 | 最速・最安 |
| **GPT-4o** | $2.50 | $10 | 汎用 |
| **GPT-4o-mini** | $0.15 | $0.60 | 激安 |
| **Gemini 2.5 Pro** | $1.25 | $5 | 長文 |
| **Gemini 2.5 Flash** | $0.075 | $0.30 | 最安クラス |
| **DeepSeek-R1** | $0.55 | $2.19 | 推論タスク |

### 学生が使える無料枠
- **Google AI Studio**: Gemini 無料枠が最も寛大（1500 req/day）
- **Anthropic**: claude.ai 無料枠（回数制限あり）
- **OpenRouter**: 複数プロバイダ集約、たまに無料モデル
- **GitHub Student Pack**: 各種クレジット付与
- **Kaggle Notebooks**: T4/P100 GPU 週30時間無料
- **Google Colab**: T4 16GB 無料（制限あり）
- **Lightning.ai**: GPU無料枠
- **Hugging Face Spaces**: Gradio/Streamlit無料ホスティング

## 機械学習の基礎アルゴリズム

### 教師あり学習
- **線形回帰 / ロジスティック回帰**: ベースライン必須
- **決定木 / ランダムフォレスト**: 解釈しやすい
- **XGBoost / LightGBM / CatBoost**: Kaggle王道
- **SVM**: 小データで強い
- **ニューラルネット**: 大データで最強

### 教師なし学習
- **K-Means**: クラスタリング定番
- **DBSCAN**: ノイズ耐性クラスタ
- **PCA / t-SNE / UMAP**: 次元削減の3強
- **Isolation Forest**: 異常検知

### 深層学習の発展
- **CNN**: 画像（ResNet, EfficientNet, ConvNeXt）
- **RNN/LSTM**: 時系列（今やTransformerに押され気味）
- **Transformer**: 文章・画像・音声すべて
- **ViT (Vision Transformer)**: 画像認識の新定番
- **Diffusion Model**: 画像生成（Stable Diffusion, DALL-E）
- **GNN (Graph Neural Network)**: グラフデータ

### 重要な評価指標
| 指標 | 用途 | 注意点 |
|------|-----|--------|
| **Accuracy** | 分類 | 不均衡データで誤解を招く |
| **Precision / Recall / F1** | 分類 | 医療・不正検知で必須 |
| **AUC-ROC** | 2値分類 | 閾値独立 |
| **MAE / RMSE** | 回帰 | MAEは外れ値に強い |
| **BLEU / ROUGE** | 翻訳・要約 | 古典的 |
| **BERTScore** | 生成タスク | 意味ベース |
| **Perplexity** | 言語モデル | 低いほど良い |

## 大学生がやるべきAI/MLプロジェクト

### ポートフォリオ向け（難易度別）
- **★ Kaggle Titanic**: 入門、まずこれ
- **★★ Fine-tuning BERT**: 感情分析、LoRAでOK
- **★★ RAGチャットボット**: 大学の講義資料にQA
- **★★★ マルチモーダルAI**: Vision + LLM
- **★★★ エージェント**: LangGraphで複数ステップ自動化
- **★★★★ ゼロから実装**: nanoGPT、MiniGPT、GPT-from-scratch
- **★★★★★ 論文実装**: arXivから選んで再現

### 研究テーマのトレンド（2025-2026）
- **推論モデル**: o1/R1 系の Chain-of-Thought 内部化
- **エージェント**: 長時間タスクの自律実行
- **Mechanistic Interpretability**: AIの中身を解析（Anthropic研究）
- **Alignment**: RLHF、DPO、Constitutional AI
- **Multimodal**: Vision + Audio + Text 統合
- **Efficient Inference**: 量子化、蒸留、投機的デコーディング
- **Agentic Retrieval**: エージェントが自分で調べるRAG

### 論文の読み方（情報系学生の常識）
- **arXiv**: プレプリント置き場、全AI論文のデフォルト
- **Papers with Code**: 論文+実装コードで一気見
- **Hugging Face Papers**: 毎日のトレンド論文
- **Semantic Scholar**: 引用関係で辿る
- **Connected Papers**: 関連論文の視覚化

## 投稿で使える「情報系学生の硬派ファクト」

- 「Claude Sonnet 4.6 は1Mトークンあたり3ドル、本1冊読んで15円」
- 「DeepSeek は557万ドルで671BパラメータのMoEを訓練した」
- 「Ollamaで自分のPCにLLMを動かすのに、RTX 3060 12GBで13Bモデルが快適」
- 「uv は pip の100倍速い。もうpipに戻れない」
- 「LoRAでファインチューンすると、パラメータの1%だけ訓練すれば本体匹敵」
- 「MCP は LLM のUSB-C。ツール連携が標準化される」
- 「Contextual Retrieval でRAG性能が49%上がる」
- 「Transformer の Attention は Q・K・V の3行列で全て決まる」
- 「Google Colab の無料T4で、7Bモデルなら推論できる」
- 「Kaggle Notebooks は週30時間の無料GPU。学生の宝」
