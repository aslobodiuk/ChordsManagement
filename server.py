import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Response
from sqlalchemy.orm import selectinload
from sqlmodel import select

from api.routes import router
from db import get_session
from elasticsearch_client import index_song, create_songs_index_if_needed
from models.db_models import Song
from settings import settings

PROTOCOL = os.getenv("PROTOCOL")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", 8000))

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_songs_index_if_needed()
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

def run_server():
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
@app.get("/", include_in_schema=False)
def root():
    """Health check"""
    return Response("Server is running!", status_code=200)
