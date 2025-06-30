from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://chordsdb_admin:Gfhfdjpbr19!@localhost:5432/chordsdb"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    PROTOCOL: str = "http"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
