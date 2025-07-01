from collections import defaultdict
from enum import Enum
from typing import List, Union

from sqlalchemy import Sequence
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_
from fastapi import Query

from data_processing import convert_lyrics_into_song_lines
from elasticsearch_client import search_songs
from models.db_models import Song, Line, Artist
from models.schemas import (
    SongCreate, SongReadShort, SongRead, SongReadForEdit,
    SongReadForDisplay, SongIdsRequest, SongUpdate, ArtistCreate, ArtistRead
)

class NotFoundError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

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
        raise NotFoundError(message="Song with ID {} not found".format(song_id))
    return song

def db_find_songs_by_id(request: SongIdsRequest, session: Session) -> List[Song]:
    """
    Retrieve multiple songs by their IDs or raise NotFoundError if none found.
    """
    statement = select(Song).where(Song.id.in_(request.song_ids))
    songs = session.exec(statement).all()
    if not songs:
        raise NotFoundError(message="Songs with such IDs were not found")
    return songs

def db_find_all_songs(session: Session) -> Sequence[Song]:
    """
    Return all songs from the database (no filtering or pagination).
    """
    return session.exec(select(Song)).all()

def choose_proper_display(display, song, highlights=None):
    """
        Returns a song model formatted according to the specified display mode.

        Highlights are attached if provided. In certain modes, raw lines are also included
        for internal use (e.g., editing or display rendering).

        Args:
            display: Selected display mode (enum).
            song: Original `Song` object from the DB.
            highlights: Optional search highlights from Elasticsearch.

        Returns:
            An instance of the appropriate `SongRead*` model.
    """
    display_mode = DISPLAY_MODES[display]
    song_out = display_mode.model_validate(song)
    if highlights:
        song_out.highlights = highlights
    if display in [SongDisplayMode.for_edit, SongDisplayMode.for_display]:
        song_out._lines = song.lines  # manually assign hidden data
        return song_out
    return song_out

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
    return choose_proper_display(display, song)

def db_find_songs(skip: int, limit: int, search: str, artists: List[int], session: Session):
    """
        Fetches songs with pagination and optional Elasticsearch-based search.

        If `search` is provided, returns songs matching the search query using
        Elasticsearch relevance order. Otherwise, returns paginated results
        directly from the database.

        Returns:
            A tuple: (list of Song objects, raw search results or empty list).
    """
    if search:
        search_result = search_songs(search, limit=limit + skip)
        if not search_result:
            return [], []

        song_ids = [highlight['id'] for highlight in search_result]

        conditions = [Song.id.in_(song_ids)]
        if artists:
            conditions.append(Song.artist_id.in_(artists))
        statement = (
            select(Song)
            .where(and_(*conditions))
            .options(selectinload(Song.lines).selectinload(Line.chords))
        )
        songs = session.exec(statement).all()

        # Sort songs to match ES relevance order
        id_to_index = {str(id): i for i, id in enumerate(song_ids)}
        songs.sort(key=lambda s: id_to_index.get(str(s.id), 0))

        return songs, search_result

    # fallback for no search
    statement = (
        select(Song)
        .offset(skip)
        .limit(limit)
        .options(selectinload(Song.lines).selectinload(Line.chords))
    )
    if artists:
        statement = statement.where(Song.artist_id.in_(artists))
    return session.exec(statement).all(), []

def db_read_songs(
    skip: int,
    limit: int,
    search: str,
    session: Session,
    artists: List[int] = Query(default=[]),
    display: SongDisplayMode = Query(default=SongDisplayMode.full)
) -> Union[List[SongRead], List[SongReadShort], List[SongReadForEdit], List[SongReadForDisplay]]:
    """
    Returns a list of songs with optional search and display mode.

    If `search` is provided, fetches matching songs from Elasticsearch
    and adds field highlights. Results are formatted based on `display`.

    Args:
        skip: Records to skip (pagination).
        limit: Max number of songs to return.
        search: Search term (optional).
        session: Active DB session.
        artists: Artist IDs to include (optional).
        display: Output format (e.g., full, short).

    Returns:
        List of song representations with optional highlights.
    """
    songs, search_result = db_find_songs(skip, limit, search, artists, session)
    highlights = defaultdict(list)
    for data in search_result:
        highlights[int(data['id'])] = data['highlight']
    return [choose_proper_display(display, song, highlights[song.id]) for song in songs]


def db_create_song(song_in: SongCreate, session: Session) -> Song:
    """
    Create a new song by parsing lyrics into lines and chords.
    Commits the new song to the database.
    """
    song = convert_lyrics_into_song_lines(
        lyrics=song_in.lyrics,
        title=song_in.title,
        artist_id=song_in.artist_id
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
        song.artist_id = update_data.get("artist_id", song.artist_id)

        session.commit()
        session.refresh(song)
        return song

    # Handle title/artist if lyrics not provided
    song.title = update_data.get("title", song.title)
    song.artist_id = update_data.get("artist_id", song.artist_id)

    session.commit()
    session.refresh(song)
    return song

def db_delete_songs(request: SongIdsRequest, session: Session) -> List[Song]:
    """
    Delete all songs matching the provided list of IDs.
    Returns deleted song data.
    """
    songs = db_find_songs_by_id(request, session)
    for song in songs:
        session.delete(song)
    session.commit()
    return songs

def db_read_artists(skip: int, limit: int, session: Session) -> Sequence[Artist]:
    """Fetch a paginated list of artists with their related songs."""
    statement = (
        select(Artist)
        .offset(skip)
        .limit(limit)
        .options(selectinload(Artist.songs))
    )
    return session.exec(statement).all()

def db_read_artist(artist_id: int, session: Session) -> Artist:
    """Retrieve a single artist by ID or raise NotFoundError if not found."""
    artist: Artist | None = session.get(Artist, artist_id)
    if artist is None:
        raise NotFoundError(message="Artist with ID {} not found".format(artist_id))
    return artist

def db_create_artist(payload: ArtistCreate, session: Session) -> Artist:
    """Create and persist a new artist from the given payload."""
    artist = Artist(name=payload.name)
    session.add(artist)
    session.commit()
    session.refresh(artist)
    return artist

def db_delete_artist(artist_id: int, session: Session):
    """Delete an artist by ID or raise NotFoundError if not found."""
    artist: Artist | None = session.get(Artist, artist_id)
    if artist is None:
        raise NotFoundError(message="Artist with ID {} not found".format(artist_id))
    session.delete(artist)
    session.commit()
    return artist