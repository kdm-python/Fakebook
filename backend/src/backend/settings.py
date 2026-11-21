from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_DIR / ".env"),
        env_prefix="FAKEBOOK_",
        extra="ignore",
    )

    app_name: str = "Python Exercise Runner"
    host: str = "127.0.0.1"
    port: int = 8000
    forwarded_allow_ips: str = "127.0.0.1"
    frontend_dir: Path = PROJECT_DIR / "frontend"
    exercise_dir: Path = BACKEND_DIR / "exercises"
    run_timeout_seconds: float = Field(default=60.0, gt=0)
    max_output_bytes: int = Field(default=100_000, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
