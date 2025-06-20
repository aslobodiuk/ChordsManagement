from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

# Dependency: Database session
def get_session():
    with Session(engine) as session:
        yield session