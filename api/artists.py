from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select

from db import get_session
from elasticsearch_client import index_artist, es, index_song
from models.db_models import Artist
from models.operations import db_read_artists, NotFoundError, db_read_artist, db_create_artist, db_delete_artist, \
    db_edit_artist
from models.schemas import ArtistReadWithSongs, ArtistRead, ArtistCreate, ArtistUpdate
from settings import get_settings

router = APIRouter(tags=["Artists"], prefix="/artists")

settings = get_settings()

@router.get(
    path="/",
    response_model=List[ArtistReadWithSongs],
    summary="Artist list"
)
def read_artists(skip: int = 0, limit: int = 100, search: str = "", session: Session = Depends(get_session)):
    """
        Retrieve a paginated list of artists along with their songs.

        Parameters
        ----------
        `skip`: `int`, `optional`
            Number of records to skip for pagination (default is 0).\n
        `limit`: `int`, `optional`
            Maximum number of records to return (default is 100).\n
        `search`: `str`, `optional`
            A case-insensitive search query string.
            Matches are performed across artist names and his song's titles.
            If a match is found, highlighted snippets will be included in the response.
            When specified, songs are ordered by relevance instead of creation order.\n
        `session`: `Session`
            Active database session (injected dependency).

        Returns
        -------
        `List[ArtistReadWithSongs]`
            A list of artists with their associated songs.
    """
    return db_read_artists(skip=skip, limit=limit, search=search, session=session)

@router.get(
    path="/{artist_id}",
    response_model=ArtistReadWithSongs,
    summary="Artist details"
)
def read_artist(artist_id: int, session: Session = Depends(get_session)):
    """
        Retrieve a single artist by ID, including their associated songs.

        Parameters
        ----------
        `artist_id`: `int`
            Unique identifier of the artist to retrieve.\n
        `session`: `Session`
            Active database session (injected dependency).

        Returns
        -------
        `ArtistReadWithSongs`
            The artist data including a list of their songs.

        Raises
        ------
        `HTTPException`
            If no artist is found with the given ID, returns 404 error.
    """
    try:
        return db_read_artist(artist_id, session)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Artist not found")

@router.post(
    path="/",
    response_model=ArtistRead,
    summary="Artist create"
)
def create_artist(payload: ArtistCreate, session: Session = Depends(get_session)):
    """
        Create a new artist.

        Parameters
        ----------
        `payload`: `ArtistCreate`
            Object containing the name of the artist to create.\n
        `session`: `Session`, `optional`
            Database session dependency.

        Returns
        -------
        `ArtistRead`
            The created artist, including its generated ID.

        Raises
        ------
        `HTTPException` (400)
            If an artist with the same name already exists.
    """
    if session.exec(select(Artist).where(Artist.name == payload.name)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Artist with name '{payload.name}' already exists"
        )
    artist = db_create_artist(payload, session)
    # add to Elasticsearch
    index_artist(artist)
    return artist

@router.delete(
    path="/{artist_id}",
    response_model=None,
    summary="Artist delete"
)
def delete_artist(artist_id: int, session: Session = Depends(get_session)):
    """
        Delete an artist by ID.

        Parameters
        ----------
        `artist_id` : `int`
            The ID of the artist to delete.\n
        `session` : `Session`, `optional`
            Database session dependency.

        Returns
        -------
        `Response`
            A response with HTTP 204 No Content if deletion was successful.

        Raises
        ------
        `HTTPException` (404)
            If no artist with the specified ID is found.
    """
    try:
        artist, artist_song_ids = db_delete_artist(artist_id, session)
        # delete artist and his songs from Elasticsearch
        es.delete(index=settings.ES_ARTIST_INDEX_NAME, id=str(artist.id), ignore=[404])
        for song_id in artist_song_ids:
            es.delete(index=settings.ES_SONG_INDEX_NAME, id=str(song_id), ignore=[404])
        return Response(status_code=204)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Artist with ID {artist_id} not found")

@router.put(
    path="/{artist_id}",
    response_model=ArtistReadWithSongs,
    summary="Artist update"
)
def update_artist(artist_id: int, artist_data: ArtistUpdate, session: Session = Depends(get_session)):
    """
        Update an existing artist by ID.

        Parameters
        ----------
        `artist_id` : `int`
            The ID of the artist to update.\n
        `artist_data` : `ArtistUpdate`
            The updated artist data.\n
        `session` : `Session`, optional
            Database session dependency.

        Returns
        -------
        `ArtistReadWithSongs`
            The updated artist, including associated songs.

        Raises
        ------
        `HTTPException` (404)
            If the artist with the specified ID does not exist.
    """
    try:
        artist = db_edit_artist(artist_id, artist_data, session)
        # update indexes for artist and all his songs
        index_artist(artist)
        for song in artist.songs:
            index_song(song)
        return artist
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Artist with ID {artist_id} not found")