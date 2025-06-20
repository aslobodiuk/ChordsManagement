from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, or_

from data_processing import convert_raw_data_into_song, convert_songs_to_pdf
from db import get_session
from models import Song, Line, SongRead, SongCreate, SongShort, SongIdsRequest
from utils.pdf_utils import create_pdf_base

router = APIRouter(tags=["Songs"])

@router.get(
    path="/songs",
    response_model=Union[List[SongRead], List[SongShort]],
    summary="List of songs"
)
def read_songs(
        skip: int = 0,
        limit: int = 100,
        search: str = "",
        short: bool = False,
        session: Session = Depends(get_session)
):
    """
        Retrieve a list of songs, optionally filtered and paginated.

        Parameters
        ----------
        `skip`: `int`, `optional`
            Number of records to skip for pagination (default is 0).\n
        `limit`: `int`, `optional`
            Maximum number of records to return (default is 100).\n
        `search`: `str`, `optional`
            Search string to filter songs by title or artist (case-insensitive).\n
        `short`: `bool`, `optional`
            If `True`, returns a shortened version of each song with only id, title, and artist.
            If `False`, returns full song details including lines and chords.\n
        `session`: `Session`
            Database session dependency.

        Returns
        -------
        `Union[List[SongRead], List[SongShort]]`
            List of songs matching the query. Full or short schema depending on `short` flag.
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

    songs = session.exec(statement).all()
    return [SongShort.model_validate(song) if short else SongRead.model_validate(song) for song in songs]

@router.get(
    path="/songs/{song_id}",
    response_model=SongRead,
    summary="Song details"
)
def read_song(song_id: int, session: Session = Depends(get_session)):
    """
        Retrieve a single song by its ID.

        Parameters
        ----------
        `song_id` : `int`
            Unique identifier of the song to retrieve.\n
        `session` : `Session`
            Database session dependency.

        Returns
        -------
        `SongRead`
            The song data including all lines and chords.

        Raises
        ------
        `HTTPException`
            If no song with the given ID is found (`404 Not Found`).
    """
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@router.post(
    path="/songs",
    response_model=SongRead,
    summary="Song creation"
)
def create_song(song_in: SongCreate, session: Session = Depends(get_session)):
    """
        Create a new song from raw input data.

        Parameters
        ----------
        `song_in` : `SongCreate`
            Input data containing title, artist, and raw lyrics string.\n
        `session` : `Session`
            Database session dependency.

        Returns
        -------
        `SongRead`
            The created song with all parsed lines and chords.

        Notes
        -----
        The raw lyrics string is parsed and converted into structured lines and chords
        before saving to the database.
    """
    song = convert_raw_data_into_song(song_in.title, song_in.artist, song_in.lyrics)
    session.add(song)
    session.commit()
    session.refresh(song)
    return song

@router.post(
    path="/songs/to_pdf",
    response_model=None,
    summary="Export songs to PDF"
)
def export_to_pdf(request: SongIdsRequest, session: Session = Depends(get_session)):
    """
        Export selected songs to a PDF.

        Parameters
        ----------
        `request` : `SongIdsRequest`
            Object containing list of song IDs. If list is `empty` - returns `all` songs\n
        `session` : `Session`
            Database session.

        Returns
        -------
        `StreamingResponse`
            PDF document with selected songs.

        Raises
        ------
        `HTTPException`
            If no songs are found for the given IDs (`404 Not Found`).
    """
    statement = select(Song)
    if request.song_ids:
        statement = statement.where(Song.id.in_(request.song_ids)) # todo proces "all" option correctly
    songs = session.exec(statement).all()
    if not songs:
        raise HTTPException(status_code=404, detail="Song not found")

    pdf = create_pdf_base()
    pdf_bytes = convert_songs_to_pdf(pdf, songs)

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=streamed.pdf"}
    )
