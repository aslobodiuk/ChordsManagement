from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from db import get_session
from models.operations import db_read_artists, NotFoundError, db_read_artist
from models.schemas import ArtistReadWithSongs

router = APIRouter(tags=["Artists"], prefix="/artists")

@router.get(
    path="/",
    response_model=List[ArtistReadWithSongs],
    summary="Artist list"
)
def read_songs(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """
        Retrieve a paginated list of artists along with their songs.

        Parameters
        ----------
        `skip`: `int`, `optional`
            Number of records to skip for pagination (default is 0).\n
        `limit`: `int`, `optional`
            Maximum number of records to return (default is 100).\n
        `session`: `Session`
            Active database session (injected dependency).

        Returns
        -------
        `List[ArtistReadWithSongs]`
            A list of artists with their associated songs.
    """
    return db_read_artists(skip=skip, limit=limit, session=session)

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