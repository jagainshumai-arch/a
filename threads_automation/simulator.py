"""シミュレーションモード — APIキーなしでパイプライン全体をデモ実行"""

import json
import logging
import os
import random
import time
from datetime import datetime, timedelta

from .config import PipelineConfig
from .threads_api import PostInsights

logger = logging.getLogger(__name__)

# ── シミュレーション用データ ──

SIMULATED_NICHES = {
    "美肌・スキンケア": {
        "target": "育児中の30代ママ",
        "topics": [
            "朝5分でできる時短スキンケアルーティン",
            "肌荒れの原因は洗顔方法だった",
            "1000円以下で買える最強保湿アイテム",
            "睡眠不足でも肌を守る3つの習慣",
            "紫外線対策を怠った30代の末路",
            "ワセリンだけで乗り切る冬のスキンケア",
            "皮膚科医が絶対やらないスキンケア3選",
            "子どもと一緒に使える低刺激コスメ",
        ],
    },
    "副業・AI活用": {
        "target": "副業初心者の会社員",
        "topics": [
            "ChatGPTで月5万円稼いだ具体的な方法",
            "AI副業で失敗する人の共通点3つ",
            "会社員が帰宅後30分でできるAI副業",
            "AIライティングで案件を獲得した手順",
            "Threads×AIで3ヶ月でフォロワー1万人",
            "AIツール代を回収するまでの道のり",
            "プロンプト販売で月10万円達成した話",
            "AI副業を始めて人生が変わった瞬間",
        ],
    },
}

SIMULATED_POSTS = [
    {
        "id": "sim_post_001",
        "text": "朝たった5分で肌年齢マイナス5歳。\n\n私が3ヶ月続けた方法はシンプルでした。\n\n①洗顔後すぐビタミンC美容液\n②化粧水は手で温めてから\n③日焼け止めは曇りでも必ず\n\n皮膚科で測ったら本当に-5歳。\n育児中でも5分なら続けられます。\n\n#美肌 #スキンケア #時短美容",
        "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
        "views": 12500, "likes": 285, "replies": 42, "reposts": 38, "quotes": 12,
    },
    {
        "id": "sim_post_002",
        "text": "副業で月5万円稼ぐのに特別なスキルは要らなかった。\n\n必要だったのは「毎日30分の継続」だけ。\n\nAIで投稿を作ってThreadsで発信してbioにリンク。\n3ヶ月目で月5万、半年で月20万。\n\nスキルじゃなくて仕組みが大事。\n\n#副業 #AI活用",
        "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
        "views": 28000, "likes": 580, "replies": 95, "reposts": 120, "quotes": 45,
    },
    {
        "id": "sim_post_003",
        "text": "育児中の肌荒れ、原因は化粧水じゃなかった。\n\n皮膚科で言われたのは「洗いすぎ」。\n\n朝はぬるま湯だけ、夜も泡立てネットで優しく。\nそれだけで2週間で赤みが引いた。\n\n高い化粧水より洗顔の見直し。\n\n#肌荒れ #育児ママ",
        "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
        "views": 8200, "likes": 195, "replies": 28, "reposts": 22, "quotes": 8,
    },
    {
        "id": "sim_post_004",
        "text": "AIを使えば誰でも稼げると思っていませんか？\n\n実はそんなに甘くないです。\n大切なのは継続することです。\n\n#AI #副業",
        "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
        "views": 450, "likes": 3, "replies": 0, "reposts": 0, "quotes": 0,
    },
    {
        "id": "sim_post_005",
        "text": "スキンケアって大事ですよね。\n\nみなさんはどんなスキンケアをしていますか？\n\n私はいろいろ試しています。\n\n#スキンケア",
        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
        "views": 320, "likes": 2, "replies": 1, "reposts": 0, "quotes": 0,
    },
]

GENERATED_DRAFTS = [
    {
        "post_type": "benefit",
        "hook_line": "1000円以下の保湿クリームで、肌診断スコアが20点上がった。",
        "text": "1000円以下の保湿クリームで、肌診断スコアが20点上がった。\n\n3ヶ月前まで乾燥肌で粉吹いてた私が試したのはワセリン+ハトムギ化粧水の組み合わせ。\n\n合計980円。\n\nポイントは「化粧水→ワセリン蓋」の順番を守るだけ。\n\n高いコスメ=正解じゃない。\n\n#スキンケア #プチプラコスメ #保湿",
        "topic": "プチプラ保湿",
        "target_audience": "育児中の30代ママ",
    },
    {
        "post_type": "list",
        "hook_line": "皮膚科医の友人が「絶対やめて」と言った洗顔の間違い3つ。",
        "text": "皮膚科医の友人が「絶対やめて」と言った洗顔の間違い3つ。\n\n①熱いお湯で顔を洗う→皮脂が全部流れて逆に乾燥\n②タオルでゴシゴシ拭く→摩擦で色素沈着の原因に\n③朝も洗顔料を使う→必要な油分まで落としすぎ\n\n正解は「ぬるま湯・押し拭き・朝は水だけ」。\n\n#洗顔 #美肌習慣",
        "topic": "洗顔の間違い",
        "target_audience": "育児中の30代ママ",
    },
    {
        "post_type": "story",
        "hook_line": "産後の肌荒れで鏡を見るのが怖かった。",
        "text": "産後の肌荒れで鏡を見るのが怖かった。\n\n赤ちゃんの世話で睡眠は3時間。顔中ニキビだらけ。\n\n変わったきっかけは皮膚科で言われた一言。\n「洗いすぎです」\n\n朝の洗顔をやめて、保湿だけに変えた。\n2週間で赤みが消えて、1ヶ月で肌質が変わった。\n\n引き算のケアが正解だった。\n\n#産後肌荒れ #スキンケア",
        "topic": "産後スキンケア",
        "target_audience": "育児中の30代ママ",
    },
    {
        "post_type": "how_to",
        "hook_line": "寝る前5分のケアで、翌朝の肌が別人になる方法。",
        "text": "寝る前5分のケアで、翌朝の肌が別人になる方法。\n\nStep1: ぬるま湯で30秒だけ洗顔\nStep2: 化粧水をハンドプレスで3回重ね付け\nStep3: ワセリンを薄く蓋\n\nこれだけ。所要時間5分。\n\n1週間続けたら夫に「肌きれいになった？」って言われた。\n\n高いナイトクリームより、この3ステップ。\n\n#ナイトケア #時短美容",
        "topic": "ナイトケアルーティン",
        "target_audience": "育児中の30代ママ",
    },
    {
        "post_type": "before_after",
        "hook_line": "スキンケアを「引き算」にしたら、月のコスメ代が1.5万→2000円になった。",
        "text": "スキンケアを「引き算」にしたら、月のコスメ代が1.5万→2000円になった。\n\nしかも肌の調子は以前より良い。\n\nやめたこと:\n・高級美容液 → ハトムギ化粧水に変更\n・洗顔2回 → 朝はぬるま湯のみ\n・パック毎日 → 週1に減らす\n\n足すより引く。\n節約と美肌は両立できる。\n\n#節約美容 #スキンケア",
        "topic": "コスメ代節約",
        "target_audience": "育児中の30代ママ",
    },
]


class SimulatedThreadsAPI:
    """Threads APIのシミュレーション"""

    def __init__(self):
        self.posts = list(SIMULATED_POSTS)
        self._next_id = 100

    def get_my_posts(self, limit=25):
        return [{"id": p["id"], "text": p["text"], "timestamp": p["timestamp"]}
                for p in self.posts[:limit]]

    def get_post_insights(self, post_id):
        post = next((p for p in self.posts if p["id"] == post_id), None)
        if post:
            return PostInsights(
                post_id=post_id,
                views=post["views"],
                likes=post["likes"],
                replies=post["replies"],
                reposts=post["reposts"],
                quotes=post.get("quotes", 0),
            )
        return PostInsights(post_id=post_id)

    def create_text_post(self, text):
        self._next_id += 1
        post_id = f"sim_post_{self._next_id:03d}"
        new_post = {
            "id": post_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "views": random.randint(500, 5000),
            "likes": random.randint(5, 150),
            "replies": random.randint(0, 30),
            "reposts": random.randint(0, 20),
            "quotes": random.randint(0, 5),
        }
        self.posts.insert(0, new_post)
        return post_id


class SimulatedAIClient:
    """AI APIのシミュレーション（事前定義レスポンスを返す）"""

    def generate(self, prompt, system="", max_tokens=2000):
        # リサーチ分析リクエスト
        if "trending_topics" in prompt:
            return json.dumps({
                "trending_topics": [
                    "プチプラスキンケアの見直し",
                    "朝のスキンケア時短術",
                    "皮膚科医が教えるNG習慣",
                    "産後の肌荒れ対策",
                    "季節の変わり目スキンケア",
                ],
                "recommended_angles": [
                    "数字で見せるBefore/After",
                    "「やめたこと」リスト型",
                    "皮膚科医の一言系ストーリー",
                    "1000円以下チャレンジ",
                    "夫・子どもの反応エピソード",
                ],
                "competitor_patterns": [
                    "1行目に具体的な数字（-5歳、月5万など）",
                    "ストーリー型は保存率が高い",
                    "リスト型（3選）は安定してviews獲得",
                    "体験談+具体数字の組み合わせが最強",
                ],
                "analysis": "高パフォーマンス投稿は全て1行目に具体的数字がある。"
                           "低パフォーマンスは問いかけ型や抽象的な内容。"
                           "ターゲット明示+PREP法の組み合わせが最も安定。",
            }, ensure_ascii=False)

        # 投稿生成リクエスト
        if "hook_line" in prompt and "full_text" in prompt:
            idx = random.randint(0, len(GENERATED_DRAFTS) - 1)
            draft = GENERATED_DRAFTS[idx]
            return json.dumps({
                "hook_line": draft["hook_line"],
                "full_text": draft["text"],
            }, ensure_ascii=False)

        # 失敗分析リクエスト
        if "失敗の原因" in prompt or "伸びませんでした" in prompt:
            return ("・1行目にベネフィットがなく、読者が読む理由がない\n"
                    "・ターゲットが不明確で「誰に向けた投稿か」が伝わらない\n"
                    "・具体的な数字や体験がなく、抽象的で浅い内容になっている")

        return "シミュレーション応答です。"


def run_simulation(niche: str = "美肌・スキンケア", target: str = "育児中の30代ママ"):
    """フルパイプラインのシミュレーション実行"""
    from .researcher import Researcher, ResearchResult
    from .composer import Composer
    from .publisher import Publisher
    from .fetcher import Fetcher

    data_dir = "threads_automation/data"
    os.makedirs(os.path.join(data_dir, "reports"), exist_ok=True)

    sim_threads = SimulatedThreadsAPI()
    sim_ai = SimulatedAIClient()

    print("=" * 60)
    print("  Threads × AI 自動収益化パイプライン【シミュレーション】")
    print("=" * 60)
    print(f"  ニッチ: {niche}")
    print(f"  ターゲット: {target}")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Step 1: インサイト取得（フェッチ） ──
    print("\n" + "─" * 60)
    print("📊 Step 1/6: インサイト取得（Fetcher）")
    print("─" * 60)
    posts = sim_threads.get_my_posts(limit=10)
    print(f"  取得投稿数: {len(posts)}件")
    print()
    print(f"  {'ID':<16} {'Views':>8} {'Likes':>6} {'Replies':>8} {'ER':>7}  1行目")
    print(f"  {'─'*16} {'─'*8} {'─'*6} {'─'*8} {'─'*7}  {'─'*20}")
    for p in posts:
        ins = sim_threads.get_post_insights(p["id"])
        er = (ins.likes + ins.replies + ins.reposts) / max(ins.views, 1) * 100
        first_line = p["text"].split("\n")[0][:30]
        print(f"  {p['id']:<16} {ins.views:>8,} {ins.likes:>6} {ins.replies:>8} {er:>6.2f}%  {first_line}")
    time.sleep(1)

    # ── Step 2: パフォーマンス分析 ──
    print("\n" + "─" * 60)
    print("📈 Step 2/6: パフォーマンス分析（Analyst）")
    print("─" * 60)
    all_insights = []
    for p in posts:
        ins = sim_threads.get_post_insights(p["id"])
        er = (ins.likes + ins.replies + ins.reposts) / max(ins.views, 1) * 100
        all_insights.append({"id": p["id"], "text": p["text"], "er": er,
                             "views": ins.views, "likes": ins.likes})

    all_insights.sort(key=lambda x: x["er"], reverse=True)
    avg_er = sum(i["er"] for i in all_insights) / len(all_insights)
    total_views = sum(i["views"] for i in all_insights)
    total_likes = sum(i["likes"] for i in all_insights)

    print(f"  平均エンゲージメント率: {avg_er:.2f}%")
    print(f"  総表示回数: {total_views:,}")
    print(f"  総いいね: {total_likes:,}")
    print()

    top = all_insights[:2]
    low = [i for i in all_insights if i["er"] < 1.0]

    print("  🏆 高パフォーマンス投稿:")
    for t in top:
        first_line = t["text"].split("\n")[0][:40]
        print(f"    ER={t['er']:.2f}% | {first_line}")

    print()
    print("  ⚠️  低パフォーマンス投稿:")
    for l in low:
        first_line = l["text"].split("\n")[0][:40]
        print(f"    ER={l['er']:.2f}% | {first_line}")

    if low:
        print()
        print("  💡 失敗要因分析（AI）:")
        analysis = sim_ai.generate("失敗の原因を分析")
        for line in analysis.strip().split("\n"):
            print(f"    {line}")
    time.sleep(1)

    # ── Step 3: リサーチ ──
    print("\n" + "─" * 60)
    print("🔍 Step 3/6: トレンドリサーチ（Researcher）")
    print("─" * 60)
    research_raw = sim_ai.generate("trending_topics")
    research_data = json.loads(research_raw)

    print("  🔥 トレンドトピック:")
    for i, topic in enumerate(research_data["trending_topics"], 1):
        print(f"    {i}. {topic}")

    print()
    print("  💡 おすすめの切り口:")
    for i, angle in enumerate(research_data["recommended_angles"], 1):
        print(f"    {i}. {angle}")

    print()
    print("  📊 競合の成功パターン:")
    for pattern in research_data["competitor_patterns"]:
        print(f"    ・{pattern}")

    print()
    print(f"  📝 総合分析: {research_data['analysis']}")
    time.sleep(1)

    # ── Step 4: 投稿作成 ──
    print("\n" + "─" * 60)
    print("✍️  Step 4/6: 投稿作成（Writer）")
    print("─" * 60)
    drafts = GENERATED_DRAFTS
    print(f"  生成投稿数: {len(drafts)}本\n")
    for i, draft in enumerate(drafts, 1):
        print(f"  ┌─── 投稿 {i} [{draft['post_type']}] ───")
        print(f"  │ ターゲット: {draft['target_audience']}")
        print(f"  │ フック: {draft['hook_line']}")
        print(f"  │")
        for line in draft["text"].split("\n"):
            print(f"  │ {line}")
        print(f"  │")
        print(f"  │ 文字数: {len(draft['text'])}字")
        print(f"  └{'─' * 40}")
        print()
    time.sleep(1)

    # ── Step 5: 投稿公開 ──
    print("─" * 60)
    print("📤 Step 5/6: 投稿公開（Poster）")
    print("─" * 60)
    published = []
    for i, draft in enumerate(drafts, 1):
        post_id = sim_threads.create_text_post(draft["text"])
        published.append(post_id)
        first_line = draft["hook_line"][:35]
        print(f"  ✅ 投稿{i} 公開完了: {post_id} | {first_line}")
        if i < len(drafts):
            time.sleep(0.5)
    print(f"\n  合計 {len(published)} 件の投稿を公開")
    time.sleep(1)

    # ── Step 6: スーパーバイザーレポート ──
    print("\n" + "─" * 60)
    print("🎯 Step 6/6: スーパーバイザーレポート")
    print("─" * 60)
    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │         ヘルスチェックサマリー            │")
    print("  ├──────────────────┬───────┬───────────────┤")
    print("  │ 項目             │ 値    │ 判定          │")
    print("  ├──────────────────┼───────┼───────────────┤")
    print(f"  │ 本日の投稿数     │ {len(published):>5} │ ✅ 正常        │")
    print(f"  │ 平均ER           │ {avg_er:>4.1f}% │ {'✅ 良好' if avg_er > 2 else '⚠️  要改善'}       │")
    print(f"  │ 低調投稿率       │ {len(low)/len(all_insights)*100:>4.0f}% │ {'✅ 正常' if len(low)/len(all_insights) < 0.3 else '⚠️  要改善'}       │")
    print(f"  │ 下書きストック   │ {len(drafts):>5} │ ✅ 十分        │")
    print(f"  │ リサーチ鮮度     │ 本日  │ ✅ 最新        │")
    print("  └──────────────────┴───────┴───────────────┘")
    print()
    print("  📋 次回アクション:")
    print("    1. 公開した5投稿のインサイトを6時間後に /fetcher で取得")
    print("    2. ER上位の投稿をテンプレ化して /writer に反映")
    print("    3. 低調投稿のリライト版を /writer で作成")
    print()

    # レポート保存
    report = {
        "cycle_time": datetime.now().isoformat(),
        "mode": "simulation",
        "niche": niche,
        "target_audience": target,
        "posts_analyzed": len(posts),
        "avg_engagement_rate": round(avg_er, 2),
        "total_views": total_views,
        "total_likes": total_likes,
        "top_performers": [{"id": t["id"], "er": round(t["er"], 2)} for t in top],
        "low_performers": [{"id": l["id"], "er": round(l["er"], 2)} for l in low],
        "new_posts_published": len(published),
        "published_ids": published,
        "trending_topics": research_data["trending_topics"],
        "drafts_generated": len(drafts),
    }
    report_path = os.path.join(data_dir, "reports",
                               f"sim_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 下書き保存
    drafts_path = os.path.join(data_dir,
                               f"drafts_{datetime.now().strftime('%Y%m%d')}.json")
    with open(drafts_path, "w", encoding="utf-8") as f:
        json.dump(GENERATED_DRAFTS, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("  パイプライン完了")
    print(f"  レポート保存先: {report_path}")
    print(f"  下書き保存先:   {drafts_path}")
    print("=" * 60)

    return report
