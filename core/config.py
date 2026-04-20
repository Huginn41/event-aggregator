from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_connection_string: str | None = None
    postgres_host: str | None = None
    postgres_port: int = 5432
    postgres_username: str | None = None
    postgres_password: str | None = None
    postgres_database_name: str | None = None

    events_api_key: str = ""
    events_api_url: str = "http://events-provider.dev-2.python-labs.ru"

    sync_interval_hours: int = 24
    seats_cache_ttl_seconds: int = 30

    @property
    def db_url(self) -> str:

        if self.postgres_connection_string:
            url = self.postgres_connection_string
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url

        return (
            f"postgresql+asyncpg://{self.postgres_username}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database_name}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()