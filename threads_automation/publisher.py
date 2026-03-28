"""投稿モジュール — 下書きをThreadsに公開"""

import json
import logging
import os
import time
from datetime import datetime

from .composer import DraftPost
from .threads_api import ThreadsAPIClient

logger = logging.getLogger(__name__)


class Publisher:
    """投稿の公開・履歴管理"""

    def __init__(self, threads: ThreadsAPIClient, data_dir: str = "data"):
        self.threads = threads
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "publish_history.json")

    def publish(self, draft: DraftPost) -> str | None:
        """下書きをThreadsに投稿し、投稿IDを返す"""
        try:
            post_id = self.threads.create_text_post(draft.text)
            self._save_to_history(draft, post_id)
            logger.info("Published post %s: %s", post_id, draft.hook_line)
            return post_id
        except Exception as e:
            logger.error("Failed to publish: %s", e)
            return None

    def publish_batch(self, drafts: list[DraftPost],
                      interval_seconds: int = 300) -> list[str]:
        """複数の下書きを間隔を空けて順次投稿"""
        published_ids = []
        for i, draft in enumerate(drafts):
            post_id = self.publish(draft)
            if post_id:
                published_ids.append(post_id)
            if i < len(drafts) - 1:
                logger.info("Waiting %d seconds before next post...", interval_seconds)
                time.sleep(interval_seconds)
        return published_ids

    def _save_to_history(self, draft: DraftPost, post_id: str):
        """投稿履歴をJSONに保存"""
        os.makedirs(self.data_dir, exist_ok=True)
        history = self._load_history()
        history.append({
            "post_id": post_id,
            "text": draft.text,
            "topic": draft.topic,
            "post_type": draft.post_type,
            "target_audience": draft.target_audience,
            "hook_line": draft.hook_line,
            "published_at": datetime.now().isoformat(),
        })
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _load_history(self) -> list[dict]:
        if os.path.exists(self.history_file):
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        return []
