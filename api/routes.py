from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from data_processing import convert_songs_to_pdf
from db import get_session
from elasticsearch_client import index_song, es
from models.operations import (
    db_create_song, db_read_song, NotFoundError, db_read_songs, SongDisplayMode,
    db_delete_songs, db_edit_song, db_find_songs_by_id, db_find_all_songs
)
from models.schemas import (
    SongRead, SongCreate, SongReadShort, SongIdsRequest, SongReadForEdit, SongReadForDisplay, SongUpdate
)
from settings import get_settings
from utils.pdf_utils import create_pdf_base

router = APIRouter(tags=["Songs"], prefix="/songs")

settings = get_settings()

@router.get(
    path="/",
    response_model=Union[List[SongRead], List[SongReadShort], List[SongReadForEdit], List[SongReadForDisplay]],
    summary="Song list"
)
def read_songs(
        skip: int = 0,
        limit: int = 100,
        search: str = "",
        display: SongDisplayMode = Query(default=SongDisplayMode.full),
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
        `display` : `SongDisplayMode`, `optional`
            Controls which fields are included in the response.\n
        `session`: `Session`
            Database session dependency.

        Returns
        -------
        `Union[List[SongRead], List[SongReadShort], List[SongReadForEdit], List[SongReadForDisplay]]`
            List of songs matching the query.
    """
    return db_read_songs(skip=skip, limit=limit, search=search, display=display, session=session)

@router.get(
    path="/{song_id}",
    response_model=Union[SongRead, SongReadShort, SongReadForDisplay, SongReadForEdit],
    summary="Song details"
)
def read_song(
        song_id: int,
        display: SongDisplayMode = Query(default=SongDisplayMode.full),
        session: Session = Depends(get_session)
):
    """
        Retrieve a single song by its ID.

        Parameters
        ----------
        `song_id` : `int`
            Unique identifier of the song to retrieve.\n
        `display` : `SongDisplayMode`, `optional`
            Controls which fields are included in the response.\n
        `session` : `Session`
            Database session dependency.

        Returns
        -------
        `Union[SongRead, SongReadShort, SongReadForDisplay, SongReadForEdit]`
            The song data including all lines and chords.

        Raises
        ------
        `HTTPException`
            If no song with the given ID is found (`404 Not Found`).
    """
    try:
        return db_read_song(song_id, session, display)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Song not found")

@router.post(
    path="/",
    response_model=SongRead,
    summary="Song create"
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
    song = db_create_song(song_in, session)
    # add to Elasticsearch
    index_song(song)
    return song

@router.put(
    path="/{song_id}",
    response_model=SongRead,
    summary="Song update"
)
def update_song(song_id: int, song_data: SongUpdate, session: Session = Depends(get_session)):
    """
        Update an existing song with new metadata or lyrics.

        This endpoint supports partial updates. If the `lyrics` field is provided, all existing lines and chords
        are deleted and replaced with new ones derived from the updated lyrics. If only `title` or `artist` are
        provided, they are updated without affecting the song structure.

        Parameters
        ----------
        `song_id` : `int`
            The ID of the song to update.\n
        `song_data` : `SongUpdate`
            A Pydantic model containing the fields to update. Fields not set will be ignored.\n
        `session` : `Session`
            Database session dependency, injected by FastAPI.

        Returns
        -------
        `SongRead`
            The updated song with full detail.

        Raises
        ------
        `HTTPException`
            If no song is found with the provided ID.
        """
    try:
        song = db_edit_song(song_id, song_data, session)
        # update in Elasticsearch
        index_song(song)
        return song
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Song not found")

@router.delete(
    path="/",
    response_model=List[SongRead],
    summary="Song delete"
)
def delete_songs(
    request: SongIdsRequest = Body(...),
    session: Session = Depends(get_session)
):
    """
    Delete multiple songs by their IDs.

    Parameters
    ----------
    `request` : `SongIdsRequest`
        The request body containing a list of song IDs to delete.\n
    `session` : `Session`
        Database session dependency.

    Returns
    -------
    `List[SongRead]`
        A list of deleted songs' data.

    Raises
    ------
    `HTTPException`
        If none of the specified songs are found (HTTP 404).
    """
    try:
        songs = db_delete_songs(request, session)
        # remove from Elasticsearch
        for song in songs:
            es.delete(index=settings.ES_INDEX_NAME, id=str(song.id), ignore=[404])
        return songs
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Song not found")

@router.post(
    path="/to_pdf",
    response_model=None,
    summary="Export songs to PDF"
)
def export_to_pdf(request: SongIdsRequest = None, session: Session = Depends(get_session)):
    """
        Export selected songs to a PDF.

        Parameters
        ----------
        `request` : `SongIdsRequest`, 'optional'
            Object containing list of song IDs. If not provided - returns `all` songs\n
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
    try:
        songs = db_find_songs_by_id(request, session) if request else db_find_all_songs(session)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Song not found")

    pdf = create_pdf_base()
    pdf_bytes = convert_songs_to_pdf(pdf, songs)

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=streamed.pdf"}
    )
