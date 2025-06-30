from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from sqlalchemy.orm import selectinload
from sqlmodel import select

from api.routes import router
from db import get_session
from elasticsearch_client import index_song
from models.db_models import Song


@asynccontextmanager
async def lifespan(_: FastAPI):
    session = next(get_session())
    try:
        songs = session.exec(select(Song).options(selectinload(Song.lines))).all()
        for song in songs:
            index_song(song)
        yield
    finally:
        session.close()

app = FastAPI(lifespan=lifespan, title="Chord Editor API")
app.include_router(router)

@app.get("/", include_in_schema=False)
def root():
    """Health check"""
    return Response("Server is running!", status_code=200)
