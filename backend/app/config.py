from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 数据库 — 优先用 SQLite（无需 Docker）
    DATABASE_URL: str = "sqlite+aiosqlite:///./novelwriter.db"
    USE_SQLITE: bool = True

    # LLM 提供商
    # DeepSeek — 最优，用于 Writer / Supervisor / Architect
    # .env 中对应: OPENAI_API_KEY / OPENAI_API_BASE
    DEEPSEEK_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com/v1", validation_alias="OPENAI_API_BASE")

    # Kimi 月之暗面 — 中等，用于 Inspector
    # .env 中对应: kimi_API_KEY / kimi_API_BASE
    KIMI_API_KEY: str = Field(default="", validation_alias="kimi_API_KEY")
    KIMI_BASE_URL: str = Field(default="https://api.moonshot.cn/v1", validation_alias="kimi_API_BASE")

    # Qwen 通义千问 — 轻量，用于 Guardian / Custodian
    # .env 中对应: Qwen_API_KEY / Qwen_API_BASE
    QWEN_API_KEY: str = Field(default="", validation_alias="Qwen_API_KEY")
    QWEN_BASE_URL: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", validation_alias="Qwen_API_BASE")

    # ChromaDB — Step 9 启用
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Redis — Step 8 启用（Celery 后台任务）
    REDIS_URL: str = "redis://localhost:6379/0"

    # 认证
    SECRET_KEY: str = "change-me-in-production"
    SESSION_EXPIRE_MINUTES: int = 120


settings = Settings()
