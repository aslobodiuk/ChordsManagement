from typing import List

from pydantic import PrivateAttr, computed_field, field_serializer, BaseModel
from sqlmodel import SQLModel

from data_processing import convert_song_into_raw_data, convert_song_into_formatted_data
from models.db_models import Line


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


class SongReadShort(SQLModel):
    id: int
    title: str
    artist: str


class SongReadForEdit(SQLModel):
    id: int
    title: str
    artist: str

    # Hide this from API schema and response
    _lines: List[Line] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Manually set _lines after instantiating from db object
        self._lines = data.get("lines", [])

    @computed_field  # Pydantic v2
    def lyrics(self) -> str:
        return convert_song_into_raw_data(self._lines)

    @field_serializer("lyrics")
    def serialize_lyrics(self, lyrics: str, _info):
        return lyrics


class SongReadForDisplay(SQLModel):
    id: int
    title: str
    artist: str

    # Hide this from API schema and response
    _lines: List[Line] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        # Manually set _lines after instantiating from db object
        self._lines = data.get("lines", [])

    @computed_field  # Pydantic v2
    def lyrics(self) -> str:
        return convert_song_into_formatted_data(self._lines)

    @field_serializer("lyrics")
    def serialize_lyrics(self, lyrics: str, _info):
        return lyrics


class SongCreate(BaseModel):
    title: str
    artist: str
    lyrics: str


class SongIdsRequest(BaseModel):
    song_ids: List[int]
