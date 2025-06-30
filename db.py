from sqlmodel import create_engine, Session

from settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False
)

# Dependency: Database session
def get_session():
    with Session(engine) as session:
        yield session