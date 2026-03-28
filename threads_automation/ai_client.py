"""AI クライアント — OpenAI / Anthropic 統一インターフェース"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .config import AIConfig

logger = logging.getLogger(__name__)


class AIClient:
    """OpenAI / Anthropic を切り替えて使えるAIクライアント"""

    def __init__(self, config: AIConfig):
        self.config = config

    def generate(self, prompt: str, system: str = "", max_tokens: int = 2000) -> str:
        """プロンプトに対してAI応答を生成"""
        if "claude" in self.config.model.lower():
            return self._call_anthropic(prompt, system, max_tokens)
        return self._call_openai(prompt, system, max_tokens)

    def _call_openai(self, prompt: str, system: str, max_tokens: int) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }).encode()

        req = Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.config.openai_api_key}")

        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"]
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error("OpenAI API error %s: %s", e.code, error_body)
            raise

    def _call_anthropic(self, prompt: str, system: str, max_tokens: int) -> str:
        body = json.dumps({
            "model": self.config.model,
            "max_tokens": max_tokens,
            "system": system or "あなたはThreads投稿の専門家です。",
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", self.config.anthropic_api_key)
        req.add_header("anthropic-version", "2023-06-01")

        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                return data["content"][0]["text"]
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error("Anthropic API error %s: %s", e.code, error_body)
            raise
