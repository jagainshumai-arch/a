"""Threads API クライアント — 投稿・分析取得"""

import json
import logging
import time
from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

from .config import ThreadsConfig

logger = logging.getLogger(__name__)


@dataclass
class PostInsights:
    """投稿のインサイトデータ"""
    post_id: str
    views: int = 0
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    quotes: int = 0


@dataclass
class PublishedPost:
    """公開済み投稿"""
    post_id: str
    text: str
    timestamp: str
    permalink: str = ""


class ThreadsAPIClient:
    """Threads Graph API クライアント"""

    def __init__(self, config: ThreadsConfig):
        self.config = config
        self.base_url = config.api_base

    def _request(self, method: str, endpoint: str, params: dict | None = None,
                 data: dict | None = None) -> dict:
        """APIリクエストを送信"""
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        params["access_token"] = self.config.access_token

        if method == "GET":
            url = f"{url}?{urlencode(params)}"
            req = Request(url, method="GET")
        else:
            if data:
                data.update(params)
            else:
                data = params
            body = urlencode(data).encode()
            req = Request(url, data=body, method="POST")

        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error("Threads API error %s: %s", e.code, error_body)
            raise

    # ── 投稿 ──

    def create_text_post(self, text: str) -> str:
        """テキスト投稿を作成・公開する（2ステップ）

        Returns:
            公開された投稿のID
        """
        # Step 1: メディアコンテナ作成
        container = self._request("POST", f"{self.config.user_id}/threads", data={
            "media_type": "TEXT",
            "text": text,
        })
        container_id = container["id"]
        logger.info("Container created: %s", container_id)

        # コンテナの処理待ち（最大30秒）
        for _ in range(6):
            status = self._request("GET", container_id, params={"fields": "status"})
            if status.get("status") == "FINISHED":
                break
            time.sleep(5)

        # Step 2: 公開
        result = self._request("POST", f"{self.config.user_id}/threads_publish", data={
            "creation_id": container_id,
        })
        post_id = result["id"]
        logger.info("Post published: %s", post_id)
        return post_id

    # ── 投稿一覧取得 ──

    def get_my_posts(self, limit: int = 25) -> list[dict]:
        """自分の投稿一覧を取得"""
        result = self._request("GET", f"{self.config.user_id}/threads", params={
            "fields": "id,text,timestamp,permalink,is_quote_status",
            "limit": str(limit),
        })
        return result.get("data", [])

    # ── インサイト取得 ──

    def get_post_insights(self, post_id: str) -> PostInsights:
        """投稿のインサイト（views, likes, replies, reposts, quotes）を取得"""
        result = self._request("GET", f"{post_id}/insights", params={
            "metric": "views,likes,replies,reposts,quotes",
        })
        insights = PostInsights(post_id=post_id)
        for item in result.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            value = values[0].get("value", 0) if values else 0
            if hasattr(insights, name):
                setattr(insights, name, value)
        return insights

    def get_account_insights(self, since: int, until: int) -> dict:
        """アカウントレベルのインサイトを取得"""
        result = self._request("GET", f"{self.config.user_id}/threads_insights", params={
            "metric": "views,likes,replies,reposts,quotes,followers_count",
            "since": str(since),
            "until": str(until),
        })
        account = {}
        for item in result.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            value = values[0].get("value", 0) if values else 0
            account[name] = value
        return account
