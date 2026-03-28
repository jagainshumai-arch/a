"""リサーチモジュール — 影響力のある投稿を収集・分析

Threads APIには他者の投稿検索機能がないため、以下の戦略を取る:
1. 自分の過去投稿のインサイトから伸びたパターンを抽出
2. AIに市場トレンド・競合分析を依頼
3. 手動で収集した競合投稿データ（CSV/JSON）を読み込んで分析
"""

import json
import logging
import os
from dataclasses import dataclass

from .ai_client import AIClient
from .threads_api import ThreadsAPIClient, PostInsights

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """リサーチ結果"""
    top_performing_posts: list[dict]
    trending_topics: list[str]
    recommended_angles: list[str]
    competitor_patterns: list[str]
    raw_analysis: str


class Researcher:
    """投稿リサーチ・分析エンジン"""

    def __init__(self, ai: AIClient, threads: ThreadsAPIClient, data_dir: str = "data"):
        self.ai = ai
        self.threads = threads
        self.data_dir = data_dir

    def analyze_own_posts(self) -> list[dict]:
        """自分の過去投稿をインサイト付きで分析し、高パフォーマンス投稿を特定"""
        posts = self.threads.get_my_posts(limit=50)
        enriched = []
        for post in posts:
            try:
                insights = self.threads.get_post_insights(post["id"])
                enriched.append({
                    "id": post["id"],
                    "text": post.get("text", ""),
                    "timestamp": post.get("timestamp", ""),
                    "views": insights.views,
                    "likes": insights.likes,
                    "replies": insights.replies,
                    "reposts": insights.reposts,
                    "engagement_rate": (
                        (insights.likes + insights.replies + insights.reposts)
                        / max(insights.views, 1)
                    ),
                })
            except Exception as e:
                logger.warning("Failed to get insights for %s: %s", post["id"], e)
        enriched.sort(key=lambda x: x["engagement_rate"], reverse=True)
        return enriched

    def load_competitor_data(self) -> list[dict]:
        """手動収集した競合投稿データを読み込む（data/competitor_posts.json）"""
        path = os.path.join(self.data_dir, "competitor_posts.json")
        if not os.path.exists(path):
            logger.info("No competitor data found at %s", path)
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def research(self, niche: str, target_audience: str) -> ResearchResult:
        """総合リサーチ: 自分の投稿分析 + 競合データ + AIトレンド分析"""

        # 1. 自分の高パフォーマンス投稿を取得
        own_posts = self.analyze_own_posts()
        top_posts = own_posts[:10]

        # 2. 競合データを読み込み
        competitor_data = self.load_competitor_data()

        # 3. AIにトレンド分析・角度提案を依頼
        prompt = f"""あなたはThreads×AI運用の専門家です。以下のデータを分析して、次の投稿戦略を提案してください。

【ニッチ】{niche}
【ターゲット】{target_audience}

【自分の高パフォーマンス投稿TOP10】
{json.dumps(top_posts, ensure_ascii=False, indent=2)}

【競合の投稿データ】
{json.dumps(competitor_data[:20], ensure_ascii=False, indent=2) if competitor_data else "データなし"}

以下の形式でJSON出力してください:
{{
  "trending_topics": ["トレンドトピック1", "トレンドトピック2", ...],
  "recommended_angles": ["おすすめの切り口1", "おすすめの切り口2", ...],
  "competitor_patterns": ["競合の成功パターン1", "競合の成功パターン2", ...],
  "analysis": "総合分析コメント（200文字以内）"
}}"""

        response = self.ai.generate(prompt)
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # JSONパースに失敗した場合はAI出力をそのまま使う
            parsed = {
                "trending_topics": [],
                "recommended_angles": [],
                "competitor_patterns": [],
                "analysis": response,
            }

        return ResearchResult(
            top_performing_posts=top_posts,
            trending_topics=parsed.get("trending_topics", []),
            recommended_angles=parsed.get("recommended_angles", []),
            competitor_patterns=parsed.get("competitor_patterns", []),
            raw_analysis=parsed.get("analysis", ""),
        )
