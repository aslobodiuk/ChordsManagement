from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from sqlalchemy.orm import selectinload
from sqlmodel import select

from api.songs import router as songs_router
from api.artists import router as artists_router

from db import get_session
from elasticsearch_client import index_song, es, index_artist
from models.db_models import Song, Artist
from settings import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    if es.indices.exists(index=settings.ES_SONG_INDEX_NAME):
        es.indices.delete(index=settings.ES_SONG_INDEX_NAME)

    if es.indices.exists(index=settings.ES_ARTIST_INDEX_NAME):
        es.indices.delete(index=settings.ES_ARTIST_INDEX_NAME)

    es.indices.create(index=settings.ES_SONG_INDEX_NAME, body={
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "artist": {"type": "text"},
                "lines": {"type": "text"}
            }
        }
    })

    es.indices.create(index=settings.ES_ARTIST_INDEX_NAME, body={
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "songs": {"type": "text"}
            }
        }
    })

    session = next(get_session())
    try:
        songs = session.exec(select(Song).options(selectinload(Song.lines))).all()
        for song in songs:
            index_song(song)
        artists = session.exec(select(Artist).options(selectinload(Artist.songs))).all()
        for artist in artists:
            index_artist(artist)
        yield
    finally:
        session.close()

app = FastAPI(lifespan=lifespan, title="Chord Editor API")
app.include_router(songs_router)
app.include_router(artists_router)

@app.get("/", include_in_schema=False)
def root():
    """Health check"""
    return Response("Server is running.", status_code=200)
