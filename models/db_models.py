from typing import Optional

from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship


class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str
    lines: list["Line"] = Relationship(
        back_populates="song",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Line(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["song_id"],
            ["song.id"],
            ondelete="CASCADE"
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    chords: list["Chord"] = Relationship(
        back_populates="line",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    song_id: int = Field(..., foreign_key="song.id")
    song: Song = Relationship(back_populates="lines")


class Chord(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["line_id"],
            ["line.id"],
            ondelete="CASCADE"
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    position: int
    name: str
    line_id: int = Field(..., foreign_key="line.id")
    line: Line = Relationship(back_populates="chords")
