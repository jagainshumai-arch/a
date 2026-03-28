"""メインパイプライン — CLI エントリポイント"""

import argparse
import logging
import sys

from .config import load_config
from .supervisor import Supervisor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Threads × AI 自動収益化パイプライン"
    )
    parser.add_argument(
        "--niche", required=True,
        help="発信ニッチ（例: '美肌・スキンケア', '副業・AI活用'）",
    )
    parser.add_argument(
        "--target", required=True,
        help="ターゲット読者（例: '育児中の30代ママ', '副業初心者の会社員'）",
    )
    parser.add_argument(
        "--cycles", type=int, default=1,
        help="実行サイクル数（0=無限ループ、デフォルト=1）",
    )
    parser.add_argument(
        "--mode", choices=["full", "research", "compose", "fetch", "report"],
        default="full",
        help="実行モード（デフォルト: full）",
    )
    args = parser.parse_args()

    config = load_config()

    # API設定の検証
    if not config.threads.access_token:
        logger.error("THREADS_ACCESS_TOKEN が設定されていません")
        sys.exit(1)
    if not config.threads.user_id:
        logger.error("THREADS_USER_ID が設定されていません")
        sys.exit(1)
    if not (config.ai.openai_api_key or config.ai.anthropic_api_key):
        logger.error("OPENAI_API_KEY または ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    supervisor = Supervisor(config)

    if args.mode == "full":
        supervisor.run_loop(args.niche, args.target, cycles=args.cycles)
    elif args.mode == "research":
        result = supervisor.researcher.research(args.niche, args.target)
        logger.info("Trending topics: %s", result.trending_topics)
        logger.info("Recommended angles: %s", result.recommended_angles)
        logger.info("Analysis: %s", result.raw_analysis)
    elif args.mode == "compose":
        research = supervisor.researcher.research(args.niche, args.target)
        drafts = supervisor.composer.generate_posts(research, args.niche, args.target)
        for i, d in enumerate(drafts, 1):
            print(f"\n--- Draft {i} [{d.post_type}] ---")
            print(f"Hook: {d.hook_line}")
            print(d.text)
    elif args.mode == "fetch":
        insights = supervisor.fetcher.fetch_recent_insights()
        for ins in insights:
            print(f"  {ins.post_id}: views={ins.views} likes={ins.likes} "
                  f"replies={ins.replies} reposts={ins.reposts}")
    elif args.mode == "report":
        top = supervisor.fetcher.get_top_performers()
        low = supervisor.fetcher.get_low_performers()
        print(f"\nTop performers: {len(top)}")
        for t in top[:5]:
            print(f"  {t.get('post_id')}: ER={t.get('engagement_rate', 0):.4f}")
        print(f"\nLow performers: {len(low)}")


if __name__ == "__main__":
    main()
