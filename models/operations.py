from enum import Enum
from typing import List, Union

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, or_
from fastapi import Query

from data_processing import convert_lyrics_into_song_lines
from models.db_models import Song, Line
from models.schemas import (
    SongCreate, SongReadShort, SongRead, SongReadForEdit,
    SongReadForDisplay, SongIdsRequest, SongUpdate
)

class NotFoundError(Exception):
    pass

class SongDisplayMode(str, Enum):
    short = "short"
    full = "full"
    for_edit = "for_edit"
    for_display = "for_display"

DISPLAY_MODES = {
    SongDisplayMode.short: SongReadShort,
    SongDisplayMode.full: SongRead,
    SongDisplayMode.for_edit: SongReadForEdit,
    SongDisplayMode.for_display: SongReadForDisplay,
}

def db_find_song(song_id: int, session: Session) -> Song:
    """
        Retrieve a single song by ID or raise NotFoundError.
    """
    song: Song | None = session.get(Song, song_id)
    if song is None:
        raise NotFoundError()
    return song

def db_find_songs_by_id(request: SongIdsRequest, session: Session) -> List[Song]:
    """
    Retrieve multiple songs by their IDs or raise NotFoundError if none found.
    """
    statement = select(Song).where(Song.id.in_(request.song_ids))
    songs = session.exec(statement).all()
    if not songs:
        raise NotFoundError()
    return songs

def db_find_all_songs(session: Session) -> List[Song]:
    """
    Return all songs from the database (no filtering or pagination).
    """
    return session.exec(select(Song)).all()

def db_read_song(
        song_id: int,
        session: Session,
        display: SongDisplayMode = Query(default=SongDisplayMode.full)
) -> Union[SongRead, SongReadShort, SongReadForDisplay, SongReadForEdit]:
    """
    Return a single song in a given display format.
    Supports short/full/for_edit/for_display variants.
    """
    song = db_find_song(song_id, session)
    display_mode = DISPLAY_MODES[display]
    if display in [SongDisplayMode.for_edit, SongDisplayMode.for_display]:
        songs_out = display_mode.model_validate(song)
        songs_out._lines = song.lines  # manually assign hidden data
        return songs_out

    return display_mode.model_validate(song)

def db_find_songs(skip: int, limit: int, search: str, session: Session) -> List[Song]:
    """
    Query songs with pagination and optional search in title/artist.
    Includes preloading of lines and chords.
    """
    statement = (
        select(Song)
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(Song.lines).selectinload(Line.chords)
        )
    )

    if search:
        statement = statement.where(
            or_(
                Song.title.ilike(f"%{search}%"),
                Song.artist.ilike(f"%{search}%")
            )
        )

    return session.exec(statement).all()

def db_read_songs(
    skip: int,
    limit: int,
    search: str,
    session: Session,
    display: SongDisplayMode = Query(default=SongDisplayMode.full)
) -> Union[List[SongRead], List[SongReadShort], List[SongReadForEdit], List[SongReadForDisplay]]:
    """
    Return a list of songs in the specified display mode.
    Supports short/full/for_edit/for_display formats.
    """
    songs = db_find_songs(skip, limit, search, session)
    display_mode = DISPLAY_MODES[display]
    if display in [SongDisplayMode.for_edit, SongDisplayMode.for_display]:
        songs_out: List[display_mode] = []
        for song in songs:
            song_out = display_mode.model_validate(song)
            song_out._lines = song.lines  # manually assign hidden data
            songs_out.append(song_out)
        return songs_out

    return [display_mode.model_validate(song) for song in songs]


def db_create_song(song_in: SongCreate, session: Session) -> Song:
    """
    Create a new song by parsing lyrics into lines and chords.
    Commits the new song to the database.
    """
    song = convert_lyrics_into_song_lines(
        lyrics=song_in.lyrics,
        title=song_in.title,
        artist=song_in.artist
    )
    session.add(song)
    session.commit()
    session.refresh(song)
    return song

def db_edit_song(song_id: int, song_data: SongUpdate, session: Session) -> Song:
    """
    Update a song’s fields. If lyrics are provided, all lines/chords are replaced.
    """
    song = db_find_song(song_id, session)
    update_data = song_data.model_dump(exclude_unset=True)

    if "lyrics" in update_data:
        # delete all lines and chords from song and replace them with newly created
        for line in list(song.lines):
            session.delete(line)
        song.lines.clear()

        song = convert_lyrics_into_song_lines(lyrics=update_data["lyrics"], song=song)

        song.title = update_data.get("title", song.title)
        song.artist = update_data.get("artist", song.artist)

        session.commit()
        session.refresh(song)
        return song

    # Handle title/artist if lyrics not provided
    for field, value in update_data.items():
        setattr(song, field, value)

    session.commit()
    session.refresh(song)
    return song

def db_delete_songs(request: SongIdsRequest, session: Session) -> List[SongRead]:
    """
    Delete all songs matching the provided list of IDs.
    Returns deleted song data.
    """
    songs = db_find_songs_by_id(request, session)
    for song in songs:
        session.delete(song)
    session.commit()
    return songs