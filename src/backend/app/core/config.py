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
    use_sqlite: str = "false"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    llm_api_key: str = ""
    llm_api_url: str = ""
    llm_model: str = "models/gemini-2.0-flash"

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_access_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def _sync_database_url(self) -> str:
        if self.database_url.startswith("sqlite"):
            return self.database_url.replace("+aiosqlite", "")
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    def model_post_init(self, *_args, **_kwargs):
        if not self.database_url:
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                self.database_url = db_url
            elif self.use_sqlite == "true":
                self.database_url = "sqlite+aiosqlite:///./fitness_tracker.db"
            else:
                self.database_url = (
                    f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                    f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
                )

        if not self.jwt_secret_key:
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "project-butler-dev-secret-change-in-production")

    @property
    def sync_database_url(self) -> str:
        return self._sync_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
