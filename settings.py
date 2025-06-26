from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    PROTOCOL: str = "http"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    @property
    def api_url(self) -> str:
        return f"{self.PROTOCOL}://{self.HOST}:{self.PORT}"

    class Config:
        env_file = ".env"


settings = Settings()
