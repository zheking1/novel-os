from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")

    qdrant_url: str = Field("http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(None, alias="QDRANT_API_KEY")
    qdrant_memory_collection: str = Field("novel_memory_chunks", alias="QDRANT_MEMORY_COLLECTION")
    qdrant_reference_collection: str = Field("novel_reference_chunks", alias="QDRANT_REFERENCE_COLLECTION")

    redis_host: str = Field("127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    redis_password: str | None = Field(None, alias="REDIS_PASSWORD")

    auth_mode: str = Field("dev", alias="NOVEL_OS_AUTH_MODE")
    dev_user: str = Field("admin", alias="NOVEL_OS_DEV_USER")
    dev_workspace: str = Field("default", alias="NOVEL_OS_DEV_WORKSPACE")
    dev_scopes: str = Field("admin,read,write", alias="NOVEL_OS_DEV_SCOPES")
    host: str = Field("0.0.0.0", alias="NOVEL_OS_HOST")
    port: int = Field(8787, alias="NOVEL_OS_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def dev_scope_set(self) -> set[str]:
        return {scope.strip() for scope in self.dev_scopes.split(",") if scope.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

