from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "fitness_tracker"
    database_url: str = ""

    @property
    def _sync_database_url(self) -> str:
        if self.database_url.startswith("sqlite"):
            return self.database_url
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, *_args, **_kwargs):
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )

    @property
    def sync_database_url(self) -> str:
        return self._sync_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
