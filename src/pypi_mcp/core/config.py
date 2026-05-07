"""Configuration for depcheck-mcp."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings loaded from environment."""

    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 7777
    cache_ttl: int = 300
    request_timeout: int = 30
    max_cache_size: int = 1000
    allowed_ecosystems: str = "pypi,npm"  # comma-separated list

    class Config:
        env_prefix = "DEPCHECK_"
        env_file = ".env"


settings = Settings()
