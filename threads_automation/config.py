"""設定管理モジュール"""

import os
from dataclasses import dataclass, field


@dataclass
class ThreadsConfig:
    """Threads API設定"""
    access_token: str = ""
    user_id: str = ""
    api_base: str = "https://graph.threads.net/v1.0"


@dataclass
class AIConfig:
    """AI API設定"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    model: str = "gpt-4o"  # デフォルトモデル


@dataclass
class SupervisorConfig:
    """スーパーバイザー設定"""
    check_interval_minutes: int = 60
    min_views_threshold: int = 1000
    min_likes_threshold: int = 10
    max_posts_per_day: int = 10
    auto_rewrite_low_performers: bool = True


@dataclass
class PipelineConfig:
    """パイプライン全体設定"""
    threads: ThreadsConfig = field(default_factory=ThreadsConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    supervisor: SupervisorConfig = field(default_factory=SupervisorConfig)
    data_dir: str = "data"
    log_file: str = "pipeline.log"


def load_config() -> PipelineConfig:
    """環境変数から設定を読み込む"""
    config = PipelineConfig()
    config.threads.access_token = os.getenv("THREADS_ACCESS_TOKEN", "")
    config.threads.user_id = os.getenv("THREADS_USER_ID", "")
    config.ai.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    config.ai.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    config.ai.model = os.getenv("AI_MODEL", "gpt-4o")
    config.supervisor.check_interval_minutes = int(
        os.getenv("SUPERVISOR_INTERVAL", "60")
    )
    config.data_dir = os.getenv("DATA_DIR", "data")
    return config
