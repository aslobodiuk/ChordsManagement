from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from db import get_session
from models import Song, Line, SongRead

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@router.get("/songs", response_model=List[SongRead])
def read_songs(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    statement = (
        select(Song)
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(Song.lines).selectinload(Line.chords)
        )
    )
    songs = session.exec(statement).all()
    return songs


@router.get("/songs/{song_id}", response_model=SongRead)
def read_song(song_id: int, session: Session = Depends(get_session)):
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song
