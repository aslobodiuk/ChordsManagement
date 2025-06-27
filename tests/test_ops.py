import pytest

from models.db_models import Song
from models.operations import db_find_song, NotFoundError, db_find_songs_by_id, db_find_all_songs, db_read_song, \
    SongDisplayMode, db_find_songs
from models.schemas import SongIdsRequest, SongRead, SongReadShort, SongReadForDisplay, SongReadForEdit
from tests.utils import populate_test_db


def test_db_find_song(test_session):
    songs = populate_test_db(test_session, num_songs=3)

    song = db_find_song(song_id=songs[0].id, session=test_session)
    assert song.title == songs[0].title
    assert song.artist == songs[0].artist
    assert len(song.lines) == len(songs[0].lines)

def test_db_find_song_not_found(test_session):
    with pytest.raises(NotFoundError) as exc_info:
        db_find_song(song_id=999, session=test_session)
    assert exc_info.value.message == "Song with ID 999 not found"

def test_db_find_songs_by_id(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    request = SongIdsRequest(song_ids=[songs[0].id, songs[1].id])
    found = db_find_songs_by_id(request=request, session=test_session)
    assert len(found) == 2
    assert found[0].id == songs[0].id
    assert found[1].id == songs[1].id

def test_db_find_songs_by_id_not_found(test_session):
    with pytest.raises(NotFoundError) as exc_info:
        request = SongIdsRequest(song_ids=[666, 999])
        db_find_songs_by_id(request=request, session=test_session)
    assert exc_info.value.message == "Songs with such IDs were not found"

def test_db_find_songs_by_id_partially_found(test_session):
    songs = populate_test_db(test_session, num_songs=2)
    request = SongIdsRequest(song_ids=[songs[0].id, 999])
    found = db_find_songs_by_id(request=request, session=test_session)
    assert len(found) == 1
    assert found[0].id == songs[0].id

def test_db_find_all_songs(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    found = db_find_all_songs(session=test_session)
    assert len(found) == len(songs)
    assert found[0].id == songs[0].id
    assert found[1].id == songs[1].id
    assert found[2].id == songs[2].id

def display_assertions(display: SongDisplayMode, instance, test_session):
    """This 4 tests basically test not only read song display, but read_songs display also (both use same function)"""
    songs = populate_test_db(test_session, num_songs=1)
    song = db_read_song(song_id=songs[0].id, session=test_session, display=display)
    assert song.id == songs[0].id
    assert song.title == songs[0].title
    assert song.artist == songs[0].artist
    assert isinstance(song, instance)
    return song, songs

def test_db_read_song_short(test_session):
    display_assertions(SongDisplayMode.short, SongReadShort, test_session)

def test_db_read_song_full(test_session):
    song, songs = display_assertions(SongDisplayMode.full, SongRead, test_session)
    assert len(song.lines) == len(songs[0].lines)

def test_db_read_song_for_edit(test_session):
    song, _ = display_assertions(SongDisplayMode.for_edit, SongReadForEdit, test_session)
    assert song.lyrics == "(C1)Line (C2)1 of song 1\n(C1)Line (C2)2 of song 1\n(C1)Line (C2)3 of song 1\n"

def test_db_read_song_for_display(test_session):
    song, _ = display_assertions(SongDisplayMode.for_display, SongReadForDisplay, test_session)
    assert song.lyrics == "C1   C2 \nLine 1 of song 1\nC1   C2 \nLine 2 of song 1\nC1   C2 \nLine 3 of song 1\n"

def test_db_find_songs(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    found = db_find_songs(skip=0, limit=100, search="", session=test_session)
    assert len(found) == len(songs)
    assert found[0].id == songs[0].id
    assert found[1].id == songs[1].id
    assert found[2].id == songs[2].id

def search_assertions(search, songs, test_session):
    found = db_find_songs(skip=0, limit=100, search=search, session=test_session)
    assert len(found) == 1
    assert found[0].id == songs[1].id

def test_db_find_songs_with_search_by_title(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    search_assertions(songs[1].title[4:], songs, test_session)

def test_db_find_songs_with_search_by_artist(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    search_assertions(songs[1].artist[4:], songs, test_session)