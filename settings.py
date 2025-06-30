import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://chordsdb_admin:Gfhfdjpbr19!@localhost:5432/chordsdb"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ES_INDEX_NAME: str = "songs"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    # If running tests, load .env.test
    if os.getenv("PYTHON_ENV") == "test":
        load_dotenv(".env.test")
    else:
        load_dotenv(".env")
    return Settings()
