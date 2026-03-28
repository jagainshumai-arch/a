"""シミュレーター — Claude APIで実際にAI生成 + Threads部分はモック

Anthropic APIキーがあればAI部分（リサーチ分析・投稿作成・失敗分析）は
実際のClaude APIを使用。Threads API部分はモックデータで代替する。
"""

import json
import logging
import os
import random
import time
from datetime import datetime, timedelta

from .threads_api import PostInsights

logger = logging.getLogger(__name__)

# ── モック投稿データ（Threads APIの代替）──

MOCK_POSTS = [
    {
        "id": "post_001",
        "text": "朝たった5分で肌年齢マイナス5歳。\n\n私が3ヶ月続けた方法はシンプルでした。\n\n①洗顔後すぐビタミンC美容液\n②化粧水は手で温めてから\n③日焼け止めは曇りでも必ず\n\n皮膚科で測ったら本当に-5歳。\n育児中でも5分なら続けられます。\n\n#美肌 #スキンケア #時短美容",
        "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
        "views": 12500, "likes": 285, "replies": 42, "reposts": 38,
    },
    {
        "id": "post_002",
        "text": "副業で月5万円稼ぐのに特別なスキルは要らなかった。\n\n必要だったのは「毎日30分の継続」だけ。\n\nAIで投稿を作ってThreadsで発信してbioにリンク。\n3ヶ月目で月5万、半年で月20万。\n\nスキルじゃなくて仕組みが大事。\n\n#副業 #AI活用",
        "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
        "views": 28000, "likes": 580, "replies": 95, "reposts": 120,
    },
    {
        "id": "post_003",
        "text": "育児中の肌荒れ、原因は化粧水じゃなかった。\n\n皮膚科で言われたのは「洗いすぎ」。\n\n朝はぬるま湯だけ、夜も泡立てネットで優しく。\n2週間で赤みが引いた。\n\n#肌荒れ #育児ママ",
        "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
        "views": 8200, "likes": 195, "replies": 28, "reposts": 22,
    },
    {
        "id": "post_004",
        "text": "AIを使えば誰でも稼げると思っていませんか？\n\n実はそんなに甘くないです。\n大切なのは継続することです。\n\n#AI #副業",
        "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
        "views": 450, "likes": 3, "replies": 0, "reposts": 0,
    },
    {
        "id": "post_005",
        "text": "スキンケアって大事ですよね。\n\nみなさんはどんなスキンケアをしていますか？\n\n私はいろいろ試しています。\n\n#スキンケア",
        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
        "views": 310, "likes": 2, "replies": 1, "reposts": 0,
    },
]


def _get_ai_client():
    """Anthropic APIキーがあれば実際のAIクライアントを返す"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        from .ai_client import AIClient
        from .config import AIConfig
        return AIClient(AIConfig(
            anthropic_api_key=api_key,
            model="claude-sonnet-4-20250514",
        ))
    return None


def _header(title):
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)
    print()


def _step(num, total, title):
    print()
    print(f"  [{num}/{total}] {title}")
    print("  " + "-" * 56)


def run_simulation(niche: str = "美肌・スキンケア", target: str = "育児中の30代ママ"):
    """Claude API + モックThreadsでフルパイプラインを実行"""

    ai = _get_ai_client()
    use_real_ai = ai is not None

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(os.path.join(data_dir, "reports"), exist_ok=True)

    _header("Threads × AI 自動収益化パイプライン")
    print(f"  ニッチ      : {niche}")
    print(f"  ターゲット  : {target}")
    print(f"  AI エンジン : {'Claude API (実際のAI応答)' if use_real_ai else 'モック'}")
    print(f"  Threads     : シミュレーション（モックデータ）")
    print(f"  開始時刻    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ══════════════════════════════════════════════════════
    #  Step 1/6: インサイト取得（Fetcher）
    # ══════════════════════════════════════════════════════
    _step(1, 6, "📊 インサイト取得（Fetcher）")

    for p in MOCK_POSTS:
        er = (p["likes"] + p["replies"] + p["reposts"]) / max(p["views"], 1) * 100
        tag = "🔥" if p["views"] > 10000 else "✅" if p["views"] > 3000 else "⚠️" if p["views"] > 500 else "❌"
        line1 = p["text"].split("\n")[0][:35]
        print(f"  {tag} {p['id']}  views={p['views']:>6,}  likes={p['likes']:>3}  ER={er:.1f}%  {line1}")

    insights_path = os.path.join(data_dir, "insights_history.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(MOCK_POSTS, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ {len(MOCK_POSTS)}件のインサイトを保存")

    # ══════════════════════════════════════════════════════
    #  Step 2/6: パフォーマンス分析（Analyst）
    # ══════════════════════════════════════════════════════
    _step(2, 6, "📈 パフォーマンス分析（Analyst）")

    enriched = []
    for p in MOCK_POSTS:
        er = (p["likes"] + p["replies"] + p["reposts"]) / max(p["views"], 1) * 100
        enriched.append({**p, "er": er})
    enriched.sort(key=lambda x: x["er"], reverse=True)

    top_posts = [e for e in enriched if e["views"] > 5000]
    low_posts = [e for e in enriched if e["views"] < 1000]
    avg_er = sum(e["er"] for e in enriched) / len(enriched)

    print(f"  平均ER: {avg_er:.2f}%  |  総views: {sum(e['views'] for e in enriched):,}  |  総likes: {sum(e['likes'] for e in enriched):,}")
    print()
    print(f"  🏆 高パフォーマンス: {len(top_posts)}件")
    for p in top_posts:
        print(f"     ER={p['er']:.2f}%  views={p['views']:,}  | {p['text'].split(chr(10))[0][:40]}")
    print(f"  ❌ 低パフォーマンス: {len(low_posts)}件")
    for p in low_posts:
        print(f"     ER={p['er']:.2f}%  views={p['views']:,}  | {p['text'].split(chr(10))[0][:40]}")

    # 低パフォーマンス投稿のAI分析
    if low_posts:
        print()
        if use_real_ai:
            print("  🤖 Claude APIで失敗要因を分析中...")
            for p in low_posts:
                try:
                    analysis = ai.generate(
                        f"以下のThreads投稿が伸びませんでした。失敗の原因を3つ、各1行で簡潔に指摘してください。\n\n"
                        f"投稿文: {p['text']}\n表示回数: {p['views']}  いいね: {p['likes']}",
                        system="あなたはSNSマーケティングの専門家です。簡潔に回答してください。",
                        max_tokens=300,
                    )
                    print(f"\n  📋 {p['id']} の失敗分析:")
                    for line in analysis.strip().split("\n"):
                        if line.strip():
                            print(f"     {line.strip()}")
                except Exception as e:
                    print(f"  ⚠️ AI分析エラー: {e}")
        else:
            print("  📋 失敗要因（モック）:")
            print("     ・1行目にベネフィットがない")
            print("     ・ターゲットが不明確")
            print("     ・具体的な数字・事例がない")

    # ══════════════════════════════════════════════════════
    #  Step 3/6: トレンドリサーチ（Researcher）
    # ══════════════════════════════════════════════════════
    _step(3, 6, "🔍 トレンドリサーチ（Researcher）")

    comp_path = os.path.join(data_dir, "competitor_posts.json")
    competitor_data = []
    if os.path.exists(comp_path):
        with open(comp_path, encoding="utf-8") as f:
            competitor_data = json.load(f)
        print(f"  競合データ: {len(competitor_data)}件読み込み")

    if use_real_ai:
        print("  🤖 Claude APIでトレンド分析中...")
        try:
            research_prompt = f"""あなたはThreads×AI運用の専門家です。以下の条件で分析してください。

【ニッチ】{niche}
【ターゲット】{target}
【高パフォーマンス投稿】
{json.dumps([p['text'] for p in top_posts[:3]], ensure_ascii=False)}
【競合データ】
{json.dumps(competitor_data[:5], ensure_ascii=False) if competitor_data else "なし"}

以下のJSON形式のみで出力（説明文不要）:
{{"trending_topics": ["トピック1", "トピック2", "トピック3", "トピック4", "トピック5"], "recommended_angles": ["切り口1", "切り口2", "切り口3"], "analysis": "50文字以内の総合コメント"}}"""

            raw = ai.generate(research_prompt, max_tokens=600)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            research = json.loads(raw[start:end]) if start >= 0 else json.loads(raw)
        except Exception as e:
            print(f"  ⚠️ リサーチAIエラー: {e}")
            research = {"trending_topics": [f"{niche}トレンド"], "recommended_angles": ["初心者ガイド"], "analysis": ""}
    else:
        research = {
            "trending_topics": [f"{niche}の朝ルーティン", f"{niche}×時短", f"{niche}の失敗談", "プチプラ術", "専門家の声"],
            "recommended_angles": ["Before/After数字型", "3ステップ手順", "共感ストーリー"],
            "analysis": "具体的な数字がある投稿が最も伸びる",
        }

    print()
    print("  🔥 トレンドトピック:")
    for i, t in enumerate(research.get("trending_topics", []), 1):
        print(f"     {i}. {t}")
    print("  💡 おすすめの切り口:")
    for i, a in enumerate(research.get("recommended_angles", []), 1):
        print(f"     {i}. {a}")
    if research.get("analysis"):
        print(f"  📝 分析: {research['analysis']}")

    research_path = os.path.join(data_dir, f"research_report_{datetime.now().strftime('%Y%m%d')}.json")
    with open(research_path, "w", encoding="utf-8") as f:
        json.dump(research, f, ensure_ascii=False, indent=2)

    # ══════════════════════════════════════════════════════
    #  Step 4/6: 投稿作成（Writer / Composer）
    # ══════════════════════════════════════════════════════
    _step(4, 6, "✍️  投稿作成（Writer）")

    drafts = []
    topics = research.get("trending_topics", []) + research.get("recommended_angles", [])
    post_types = ["benefit", "list", "story", "how_to", "before_after"]

    num_to_generate = min(3, len(topics)) if topics else 3

    if use_real_ai:
        print(f"  🤖 Claude APIで{num_to_generate}本の投稿を生成中...\n")
        for i in range(num_to_generate):
            topic = topics[i] if i < len(topics) else f"{niche}について"
            pt = post_types[i % len(post_types)]
            try:
                prompt = f"""以下の条件でThreads投稿を1つ作成。

トピック: {topic}
ターゲット: {target}
投稿タイプ: {pt}

ルール:
- 1行目は必ずベネフィットを明示（フック）
- PREP法（結論→理由→具体例→結論）
- 300文字以内
- 「〇〇だと思っていない？」「絶対〜！」等AIっぽい表現は禁止
- 具体的な数字・事例を入れる
- 自然な口語体
- ハッシュタグは末尾に2〜3個

JSON形式のみで出力（説明文不要）:
{{"hook_line": "1行目", "full_text": "投稿全文"}}"""

                raw = ai.generate(prompt, system="あなたはThreads投稿の専門家です。", max_tokens=500)
                start = raw.find("{")
                end = raw.rfind("}") + 1
                parsed = json.loads(raw[start:end]) if start >= 0 else json.loads(raw)

                draft = {
                    "text": parsed["full_text"],
                    "topic": topic,
                    "post_type": pt,
                    "target_audience": target,
                    "hook_line": parsed["hook_line"],
                    "status": "draft",
                    "created_at": datetime.now().isoformat(),
                }
                drafts.append(draft)

                print(f"  ┌─── 投稿 {i+1} [{pt}] ───")
                print(f"  │ トピック: {topic}")
                print(f"  │ フック: {parsed['hook_line']}")
                print(f"  │")
                for line in parsed["full_text"].split("\n"):
                    print(f"  │ {line}")
                print(f"  │")
                print(f"  │ 文字数: {len(parsed['full_text'])}字")
                print(f"  └{'─' * 45}")
                print()
            except Exception as e:
                print(f"  ⚠️ 投稿{i+1}の生成エラー: {e}")
    else:
        print("  モック投稿を生成...")
        drafts = [{
            "text": f"{niche}で結果を出す人の朝習慣3つ。\n\n①毎朝5分の〇〇\n②△△を意識する\n③□□を記録する\n\n1ヶ月続けたら変化を実感。\n\n#{niche}",
            "topic": topics[0] if topics else niche,
            "post_type": "list",
            "target_audience": target,
            "hook_line": f"{niche}で結果を出す人の朝習慣3つ。",
            "status": "draft",
        }]
        print(f"  生成: {len(drafts)}本")

    drafts_path = os.path.join(data_dir, f"drafts_{datetime.now().strftime('%Y%m%d')}.json")
    with open(drafts_path, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {len(drafts)}本の下書きを保存 → {drafts_path}")

    # ══════════════════════════════════════════════════════
    #  Step 5/6: 投稿公開（Poster）[シミュレーション]
    # ══════════════════════════════════════════════════════
    _step(5, 6, "📤 投稿公開（Poster）[シミュレーション]")
    print("  ⚠️  Threads APIトークン未設定のためシミュレーション投稿")
    print()

    published = []
    for i, draft in enumerate(drafts):
        mock_id = f"sim_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"
        mock_views = random.randint(2000, 15000)
        mock_likes = random.randint(30, 300)
        published.append({
            "post_id": mock_id,
            "text": draft["text"],
            "topic": draft.get("topic", ""),
            "post_type": draft.get("post_type", ""),
            "published_at": datetime.now().isoformat(),
            "simulated_views": mock_views,
            "simulated_likes": mock_likes,
            "status": "simulated",
        })
        print(f"  ✅ 投稿{i+1} → {mock_id}  (予測: views={mock_views:,} likes={mock_likes})")

    history_path = os.path.join(data_dir, "publish_history.json")
    existing = []
    if os.path.exists(history_path):
        with open(history_path, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    existing.extend(published)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # ══════════════════════════════════════════════════════
    #  Step 6/6: スーパーバイザーレポート
    # ══════════════════════════════════════════════════════
    _step(6, 6, "🎯 スーパーバイザーレポート")

    print()
    print("  ┌────────────────────────────────────────────┐")
    print("  │           サイクル完了サマリー               │")
    print("  ├────────────────────┬────────┬──────────────┤")
    print("  │ 項目               │ 値     │ 判定         │")
    print("  ├────────────────────┼────────┼──────────────┤")
    print(f"  │ 分析した投稿       │ {len(MOCK_POSTS):>5}件 │ ─            │")
    print(f"  │ 高パフォーマンス   │ {len(top_posts):>5}件 │ ─            │")
    print(f"  │ 低パフォーマンス   │ {len(low_posts):>5}件 │ {'✅ 正常' if len(low_posts) < 3 else '⚠️  要改善'}       │")
    print(f"  │ 平均ER             │ {avg_er:>5.1f}% │ {'✅ 良好' if avg_er > 2 else '⚠️  要改善'}       │")
    print(f"  │ 生成した下書き     │ {len(drafts):>5}本 │ ✅ 十分       │")
    print(f"  │ 投稿（シミュ）     │ {len(published):>5}件 │ ✅ 完了       │")
    print(f"  │ AIエンジン         │ {'Claude':>6} │ ✅ 接続済     │" if use_real_ai else f"  │ AIエンジン         │ {'モック':>6} │ ⚠️  未接続    │")
    print(f"  │ Threads API        │ {'モック':>6} │ ⚠️  未接続    │")
    print("  └────────────────────┴────────┴──────────────┘")
    print()
    print("  📋 次のアクション:")
    print("    1. Threads APIトークンを取得して実際に投稿を公開")
    print("    2. 6時間後に /fetcher でインサイトを取得")
    print("    3. /analyst でパフォーマンスを分析")
    print("    4. 低パフォーマンス投稿を /writer でリライト")

    # レポート保存
    report = {
        "cycle_time": datetime.now().isoformat(),
        "mode": "simulation",
        "ai_engine": "claude_api" if use_real_ai else "mock",
        "niche": niche,
        "target_audience": target,
        "posts_analyzed": len(MOCK_POSTS),
        "avg_er": round(avg_er, 2),
        "top_performers": len(top_posts),
        "low_performers": len(low_posts),
        "drafts_generated": len(drafts),
        "posts_published_sim": len(published),
        "trending_topics": research.get("trending_topics", []),
    }
    report_path = os.path.join(data_dir, "reports",
                               f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    _header("パイプライン完了")
    print("  生成ファイル:")
    print(f"    📊 {insights_path}")
    print(f"    🔍 {research_path}")
    print(f"    ✍️  {drafts_path}")
    print(f"    📤 {history_path}")
    print(f"    🎯 {report_path}")
    print()

    return report
