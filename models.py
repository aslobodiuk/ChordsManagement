from typing import Optional, List

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship

class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str
    lines: list["Line"] = Relationship(back_populates="song")


class Line(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    line: str
    chords: list["Chord"] = Relationship(back_populates="line")
    song_id: int = Field(default=None, foreign_key="song.id")
    song: Song = Relationship(back_populates="lines")


class Chord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    position: int
    chord: str
    line_id: int = Field(default=None, foreign_key="line.id")
    line: Line = Relationship(back_populates="chords")


class ChordRead(SQLModel):
    id: int
    position: int
    chord: str

class LineRead(SQLModel):
    id: int
    line: str
    chords: List[ChordRead] = []

class SongRead(SQLModel):
    id: int
    title: str
    artist: str
    lines: List[LineRead] = []


class SongCreate(BaseModel):
    title: str
    artist: str
    lyrics: str

