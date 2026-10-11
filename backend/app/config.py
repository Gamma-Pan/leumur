from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://leumur:leumur@localhost:55432/leumur'
    redis_url: str = 'redis://localhost:6379/0'
    qdrant_url: str = 'http://localhost:16333'
    llm_api_key: str = ''
    llm_model: str = 'gpt-4.1-mini'
    embedding_model: str = 'text-embedding-3-small'
    cors_origin: str = 'http://localhost:5173'
    embedding_backend: Literal['local_semantic', 'lexical'] = 'local_semantic'
    model_cache: str = '/tmp/leumur-models'
    cache_seconds: int = 3600

settings = Settings()
