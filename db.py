from sqlmodel import create_engine, Session

from settings import settings

engine = create_engine(
    settings.database_url,
    echo=False
)

# Dependency: Database session
def get_session():
    with Session(engine) as session:
        yield session