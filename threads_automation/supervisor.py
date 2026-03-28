"""スーパーバイザーモジュール — パイプライン全体の自動監視・制御"""

import json
import logging
import os
import time
from datetime import datetime

from .ai_client import AIClient
from .composer import Composer
from .config import PipelineConfig
from .fetcher import Fetcher
from .publisher import Publisher
from .researcher import Researcher
from .threads_api import ThreadsAPIClient

logger = logging.getLogger(__name__)


class Supervisor:
    """パイプライン全体を監視・自動運用するスーパーバイザー

    実行サイクル:
    1. インサイト取得（フェッチ）
    2. パフォーマンス評価
    3. 低パフォーマンス投稿の自動リライト提案
    4. 新規投稿のリサーチ→作成→投稿
    5. レポート生成
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.threads = ThreadsAPIClient(config.threads)
        self.ai = AIClient(config.ai)
        self.researcher = Researcher(self.ai, self.threads, config.data_dir)
        self.composer = Composer(self.ai)
        self.publisher = Publisher(self.threads, config.data_dir)
        self.fetcher = Fetcher(self.threads, config.data_dir)
        self.report_dir = os.path.join(config.data_dir, "reports")

    # ── メインループ ──

    def run_loop(self, niche: str, target_audience: str, cycles: int = 0):
        """自動運用ループを実行

        Args:
            niche: 発信ニッチ（例: "美肌・スキンケア"）
            target_audience: ターゲット（例: "育児中の30代ママ"）
            cycles: 実行サイクル数（0=無限ループ）
        """
        logger.info("=== Supervisor started: niche=%s, target=%s ===", niche, target_audience)
        cycle = 0
        while cycles == 0 or cycle < cycles:
            cycle += 1
            logger.info("--- Cycle %d started at %s ---", cycle, datetime.now().isoformat())
            try:
                self.run_single_cycle(niche, target_audience)
            except Exception as e:
                logger.error("Cycle %d failed: %s", cycle, e)

            if cycles == 0 or cycle < cycles:
                interval = self.config.supervisor.check_interval_minutes * 60
                logger.info("Sleeping %d minutes until next cycle...",
                            self.config.supervisor.check_interval_minutes)
                time.sleep(interval)

        logger.info("=== Supervisor finished after %d cycles ===", cycle)

    def run_single_cycle(self, niche: str, target_audience: str) -> dict:
        """1サイクルのパイプラインを実行"""
        report = {
            "cycle_time": datetime.now().isoformat(),
            "niche": niche,
            "target_audience": target_audience,
        }

        # Step 1: インサイト取得
        logger.info("[1/5] Fetching insights...")
        insights = self.fetcher.fetch_recent_insights(limit=25)
        report["posts_analyzed"] = len(insights)

        # Step 2: パフォーマンス評価
        logger.info("[2/5] Evaluating performance...")
        top = self.fetcher.get_top_performers(top_n=5)
        low = self.fetcher.get_low_performers(
            min_views=self.config.supervisor.min_views_threshold,
            min_likes=self.config.supervisor.min_likes_threshold,
        )
        report["top_performers"] = len(top)
        report["low_performers"] = len(low)

        # Step 3: 低パフォーマンス投稿のリライト
        rewritten = []
        if self.config.supervisor.auto_rewrite_low_performers and low:
            logger.info("[3/5] Rewriting %d low-performing posts...", min(len(low), 3))
            rewritten = self._rewrite_low_performers(low[:3], target_audience)
        report["rewritten_count"] = len(rewritten)

        # Step 4: リサーチ→新規投稿作成→公開
        logger.info("[4/5] Research & compose new posts...")
        research = self.researcher.research(niche, target_audience)
        drafts = self.composer.generate_posts(
            research, niche, target_audience,
            count=self.config.supervisor.max_posts_per_day,
        )
        logger.info("Generated %d drafts", len(drafts))

        published_ids = self.publisher.publish_batch(drafts, interval_seconds=300)
        report["new_posts_published"] = len(published_ids)
        report["published_ids"] = published_ids

        # Step 5: レポート生成
        logger.info("[5/5] Generating report...")
        self._save_report(report)
        self._log_summary(report)

        return report

    # ── 内部メソッド ──

    def _rewrite_low_performers(self, low_posts: list[dict],
                                target_audience: str) -> list[str]:
        """低パフォーマンス投稿を分析し、リライト版を投稿"""
        published = []
        for post in low_posts:
            text = post.get("text", "")
            if not text:
                continue

            # AIにフィードバックを生成させる
            feedback = self._analyze_failure(post)
            draft = self.composer.rewrite_post(text, feedback, target_audience)
            if draft:
                post_id = self.publisher.publish(draft)
                if post_id:
                    published.append(post_id)
        return published

    def _analyze_failure(self, post: dict) -> str:
        """低パフォーマンス投稿の失敗要因をAIで分析"""
        prompt = f"""以下のThreads投稿が伸びませんでした。失敗の原因を分析し、改善点を具体的に3つ挙げてください。

【投稿文】
{post.get('text', '')}

【パフォーマンスデータ】
- 表示回数: {post.get('views', 0)}
- いいね: {post.get('likes', 0)}
- リプライ: {post.get('replies', 0)}
- リポスト: {post.get('reposts', 0)}

箇条書きで簡潔に回答してください。"""

        return self.ai.generate(prompt)

    def _save_report(self, report: dict):
        """レポートをJSONで保存"""
        os.makedirs(self.report_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.report_dir, f"report_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Report saved to %s", path)

    def _log_summary(self, report: dict):
        """サマリーをログ出力"""
        logger.info(
            "=== Cycle Summary ===\n"
            "  Posts analyzed: %d\n"
            "  Top performers: %d\n"
            "  Low performers: %d\n"
            "  Rewritten: %d\n"
            "  New posts published: %d",
            report.get("posts_analyzed", 0),
            report.get("top_performers", 0),
            report.get("low_performers", 0),
            report.get("rewritten_count", 0),
            report.get("new_posts_published", 0),
        )
