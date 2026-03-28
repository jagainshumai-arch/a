"""フェッチモジュール — 投稿結果のインサイトを定期取得"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime

from .threads_api import ThreadsAPIClient, PostInsights

logger = logging.getLogger(__name__)


class Fetcher:
    """投稿パフォーマンスデータの取得・蓄積"""

    def __init__(self, threads: ThreadsAPIClient, data_dir: str = "data"):
        self.threads = threads
        self.data_dir = data_dir
        self.insights_file = os.path.join(data_dir, "insights_history.json")

    def fetch_recent_insights(self, limit: int = 25) -> list[PostInsights]:
        """直近の投稿のインサイトを一括取得"""
        posts = self.threads.get_my_posts(limit=limit)
        results = []
        for post in posts:
            try:
                insights = self.threads.get_post_insights(post["id"])
                results.append(insights)
                self._save_insight(insights, post.get("text", ""))
            except Exception as e:
                logger.warning("Failed to fetch insights for %s: %s", post["id"], e)
        logger.info("Fetched insights for %d posts", len(results))
        return results

    def fetch_single(self, post_id: str) -> PostInsights | None:
        """特定の投稿のインサイトを取得"""
        try:
            insights = self.threads.get_post_insights(post_id)
            self._save_insight(insights)
            return insights
        except Exception as e:
            logger.error("Failed to fetch insights for %s: %s", post_id, e)
            return None

    def get_low_performers(self, min_views: int = 1000,
                           min_likes: int = 10) -> list[dict]:
        """パフォーマンスが低い投稿を特定"""
        history = self._load_history()
        low = []
        for entry in history:
            if entry["views"] < min_views and entry["likes"] < min_likes:
                low.append(entry)
        return low

    def get_top_performers(self, top_n: int = 10) -> list[dict]:
        """エンゲージメント率上位の投稿を取得"""
        history = self._load_history()
        for entry in history:
            views = max(entry.get("views", 1), 1)
            entry["engagement_rate"] = (
                entry.get("likes", 0) + entry.get("replies", 0) + entry.get("reposts", 0)
            ) / views
        history.sort(key=lambda x: x["engagement_rate"], reverse=True)
        return history[:top_n]

    def _save_insight(self, insights: PostInsights, text: str = ""):
        """インサイトを履歴に蓄積"""
        os.makedirs(self.data_dir, exist_ok=True)
        history = self._load_history()

        # 同じpost_idがあれば更新、なければ追加
        entry = asdict(insights)
        entry["fetched_at"] = datetime.now().isoformat()
        if text:
            entry["text"] = text

        existing = next((i for i, h in enumerate(history) if h["post_id"] == insights.post_id), None)
        if existing is not None:
            # テキストは既存を保持
            if not text and "text" in history[existing]:
                entry["text"] = history[existing]["text"]
            history[existing] = entry
        else:
            history.append(entry)

        with open(self.insights_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _load_history(self) -> list[dict]:
        if os.path.exists(self.insights_file):
            with open(self.insights_file, encoding="utf-8") as f:
                return json.load(f)
        return []
