from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://chordsdb_admin:Gfhfdjpbr19!@localhost:5432/chordsdb"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    class Config:
        env_file = ".env"


settings = Settings()
