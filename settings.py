from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    PROTOCOL: str = "http"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def api_url(self) -> str:
        return f"{self.PROTOCOL}://{self.HOST}:{self.PORT}"

    class Config:
        env_file = ".env"


settings = Settings()
