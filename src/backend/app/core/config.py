import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "fitness_tracker"
    database_url: str = ""

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    openai_api_key: str = ""

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_access_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def _sync_database_url(self) -> str:
        if self.database_url.startswith("sqlite"):
            return self.database_url
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    def model_post_init(self, *_args, **_kwargs):
        if not self.database_url:
            if os.getenv("DATABASE_URL"):
                self.database_url = os.getenv("DATABASE_URL")
            elif os.getenv("USE_SQLITE") == "true":
                self.database_url = "sqlite+aiosqlite:///./fitness_tracker.db"
            else:
                self.database_url = (
                    f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                    f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
                )

        if not self.jwt_secret_key:
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "project-butler-dev-secret-change-in-production")

        if self.jwt_secret_key == "project-butler-dev-secret-change-in-production":
            pass

    @property
    def sync_database_url(self) -> str:
        return self._sync_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
