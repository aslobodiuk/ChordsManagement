from typing import List, Optional

from pydantic import PrivateAttr, computed_field, field_serializer, BaseModel, field_validator
from sqlmodel import SQLModel

from data_processing import convert_song_lines_into_raw_lyrics, convert_song_lines_into_formatted_lyrics
from models.db_models import Line

class ArtistRead(SQLModel):
    id: int
    name: str

class ChordRead(SQLModel):
    id: int
    position: int
    name: str


class LineRead(SQLModel):
    id: int
    text: str
    chords: List[ChordRead] = []


class SongRead(SQLModel):
    id: int
    title: str
    artist: ArtistRead
    highlights: Optional[dict[str, List[str]]] = None
    lines: List[LineRead] = []


class SongReadShort(SQLModel):
    id: int
    title: str
    artist: ArtistRead
    highlights: Optional[dict[str, List[str]]] = None


class SongReadForEdit(SQLModel):
    id: int
    title: str
    artist: ArtistRead
    highlights: Optional[dict[str, List[str]]] = None

    # Hide this from API schema and response
    _lines: List[Line] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Manually set _lines after instantiating from db object
        self._lines = data.get("lines", [])

    @computed_field  # Pydantic v2
    def lyrics(self) -> str:
        return convert_song_lines_into_raw_lyrics(self._lines)

    @field_serializer("lyrics")
    def serialize_lyrics(self, lyrics: str, _info):
        return lyrics


class SongReadForDisplay(SQLModel):
    id: int
    title: str
    artist: ArtistRead
    highlights: Optional[dict[str, List[str]]] = None

    # Hide this from API schema and response
    _lines: List[Line] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Manually set _lines after instantiating from db object
        self._lines = data.get("lines", [])

    @computed_field
    def lyrics(self) -> str:
        return convert_song_lines_into_formatted_lyrics(self._lines)

    @field_serializer("lyrics")
    def serialize_lyrics(self, lyrics: str, _info):
        return lyrics


class SongCreate(BaseModel):
    title: str
    artist_id: int
    lyrics: str

    @field_validator("title", "lyrics")
    def not_blank(cls, value: str, info):
        if not value.strip():
            raise ValueError(f"`{info.field_name}` must not be empty or blank")
        return value


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist_id: Optional[int] = None
    lyrics: Optional[str] = None


class SongIdsRequest(BaseModel):
    song_ids: Optional[List[int]]
