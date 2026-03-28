"""投稿作成モジュール — リサーチ結果からAIで投稿文を生成"""

import json
import logging
from dataclasses import dataclass

from .ai_client import AIClient
from .researcher import ResearchResult

logger = logging.getLogger(__name__)


@dataclass
class DraftPost:
    """下書き投稿"""
    text: str
    topic: str
    target_audience: str
    post_type: str  # "benefit", "list", "story", "how_to", "before_after"
    hook_line: str  # 1行目（フック）


class Composer:
    """AIによる投稿作成エンジン"""

    SYSTEM_PROMPT = """あなたはThreads投稿の専門家です。以下のルールを厳守してください:

【絶対ルール】
1. 1行目は必ず読者のベネフィットを明示する（フック）
2. PREP法（結論→理由→具体例→結論）で構成する
3. 300文字以内で簡潔にまとめる
4. 「〇〇だと思っていない？」「絶対〜！」などAIっぽい表現は禁止
5. 具体的な数字・体験・事例を入れる
6. ターゲットが明確にわかる内容にする
7. 自然な口語体で書く（ですます調OK、硬すぎない）
8. ハッシュタグは最後に2〜3個"""

    POST_TYPES = {
        "benefit": "読者のベネフィットを1行目に提示し、PREP法で展開",
        "list": "「〇選」形式でリスト化。各項目は1行で簡潔に",
        "story": "共感ストーリー型。Before→転機→Afterの流れ",
        "how_to": "手順型。ステップ1→2→3の具体的な方法",
        "before_after": "ビフォーアフター型。変化を数字で示す",
    }

    def __init__(self, ai: AIClient):
        self.ai = ai

    def generate_posts(self, research: ResearchResult, niche: str,
                       target_audience: str, count: int = 5) -> list[DraftPost]:
        """リサーチ結果をもとに複数の下書き投稿を生成"""
        drafts = []
        topics = research.trending_topics + research.recommended_angles
        post_types = list(self.POST_TYPES.keys())

        for i in range(min(count, len(topics) if topics else count)):
            topic = topics[i] if i < len(topics) else f"{niche}に関する投稿{i+1}"
            post_type = post_types[i % len(post_types)]

            draft = self._generate_single(topic, target_audience, post_type, research)
            if draft:
                drafts.append(draft)

        return drafts

    def _generate_single(self, topic: str, target_audience: str,
                         post_type: str, research: ResearchResult) -> DraftPost | None:
        """1つの投稿を生成"""
        type_instruction = self.POST_TYPES.get(post_type, self.POST_TYPES["benefit"])

        # 高パフォーマンス投稿があればテンプレとして参考にさせる
        reference = ""
        if research.top_performing_posts:
            top = research.top_performing_posts[0]
            reference = f"\n【参考：過去の高パフォーマンス投稿】\n{top.get('text', '')[:200]}"

        prompt = f"""以下の条件でThreads投稿を1つ作成してください。

【トピック】{topic}
【ターゲット】{target_audience}
【投稿タイプ】{type_instruction}
{reference}

以下のJSON形式で出力してください:
{{
  "hook_line": "1行目のフック文",
  "full_text": "投稿全文（300文字以内、ハッシュタグ含む）"
}}"""

        try:
            response = self.ai.generate(prompt, system=self.SYSTEM_PROMPT)
            parsed = json.loads(response)
            return DraftPost(
                text=parsed["full_text"],
                topic=topic,
                target_audience=target_audience,
                post_type=post_type,
                hook_line=parsed["hook_line"],
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse AI response for topic '%s': %s", topic, e)
            # フォールバック: レスポンス全体を投稿文として使う
            if response and len(response) <= 500:
                return DraftPost(
                    text=response,
                    topic=topic,
                    target_audience=target_audience,
                    post_type=post_type,
                    hook_line=response.split("\n")[0],
                )
            return None

    def rewrite_post(self, original_text: str, feedback: str,
                     target_audience: str) -> DraftPost | None:
        """低パフォーマンス投稿をフィードバックをもとにリライト"""
        prompt = f"""以下の投稿が伸びませんでした。フィードバックをもとにリライトしてください。

【元の投稿】
{original_text}

【改善フィードバック】
{feedback}

【ターゲット】{target_audience}

以下のJSON形式で出力してください:
{{
  "hook_line": "改善した1行目",
  "full_text": "リライト後の投稿全文（300文字以内）"
}}"""

        try:
            response = self.ai.generate(prompt, system=self.SYSTEM_PROMPT)
            parsed = json.loads(response)
            return DraftPost(
                text=parsed["full_text"],
                topic="rewrite",
                target_audience=target_audience,
                post_type="benefit",
                hook_line=parsed["hook_line"],
            )
        except Exception as e:
            logger.error("Rewrite failed: %s", e)
            return None
