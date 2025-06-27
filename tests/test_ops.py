import pytest
from pydantic import ValidationError

from models.operations import (
    NotFoundError, SongDisplayMode, db_find_song, db_find_songs_by_id,
    db_find_all_songs, db_read_song, db_find_songs, db_create_song, db_edit_song, db_delete_songs
)
from models.schemas import SongIdsRequest, SongRead, SongReadShort, SongReadForDisplay, SongReadForEdit, SongCreate, \
    SongUpdate
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

def test_db_create_song(test_session):
    song_in = SongCreate(
        title="Song Title",
        artist="Song Artist",
        lyrics="(Am)Song (Dm)Line 1\n(Am)Song (Dm)Line 2",
    )
    song = db_create_song(song_in, test_session)
    song_id = song.id
    created_song = db_find_song(song_id=song_id, session=test_session)
    assert created_song.title == "Song Title"
    assert created_song.artist == "Song Artist"
    assert len(created_song.lines) == 2

def test_db_create_song_with_empty_data(test_session):
    with pytest.raises(ValidationError) as exc_info:
        SongCreate(title="", artist="", lyrics="")

    errors = exc_info.value.errors()
    assert len(errors) == 3

    expected_fields = ["title", "artist", "lyrics"]
    for field in expected_fields:
        assert any(
            e["loc"] == (field,) and f"`{field}` must not be empty or blank" in e["msg"] for e in errors
        )

def test_db_edit_song_with_no_lyrics(test_session):
    songs = populate_test_db(test_session, num_songs=1)
    song_data = SongUpdate(title="New title", artist="New artist")
    db_edit_song(song_id=songs[0].id, song_data=song_data, session=test_session)

    created_song = db_find_song(song_id=songs[0].id, session=test_session)
    assert created_song.title == "New title"
    assert created_song.artist == "New artist"
    # Assert lyrics (lines) stayed the same
    assert [line.text for line in created_song.lines] == [line.text for line in songs[0].lines]

def test_db_edit_song_with_lyrics(test_session):
    songs = populate_test_db(test_session, num_songs=1)
    song_data = SongUpdate(title="New title", artist="New artist", lyrics="(Am)Song (Dm)Line 1\n(Am)Song (Dm)Line 2")
    db_edit_song(song_id=songs[0].id, song_data=song_data, session=test_session)

    created_song = db_find_song(song_id=songs[0].id, session=test_session)

    assert created_song.title == "New title"
    assert created_song.artist == "New artist"

    # Assert lyrics were updated correctly
    expected_lines = ["Song Line 1", "Song Line 2"]
    assert len(created_song.lines) == len(expected_lines)

    for i, line in enumerate(created_song.lines):
        assert line.text == expected_lines[i]
        assert len(line.chords) == 2
        assert line.chords[0].position == 0
        assert line.chords[0].name == "Am"
        assert line.chords[1].position == 5
        assert line.chords[1].name == "Dm"

def test_db_delete_songs(test_session):
    songs = populate_test_db(test_session, num_songs=4)
    ids_for_delete = [songs[0].id, songs[1].id]
    ids_to_remain = [songs[2].id, songs[3].id]
    request = SongIdsRequest(song_ids=ids_for_delete)
    deleted_songs = db_delete_songs(request, test_session)

    # Assert correct songs were deleted
    assert sorted([song.id for song in deleted_songs]) == sorted(ids_for_delete)

    # Assert the remaining songs are untouched
    remaining_song_ids = [song.id for song in db_find_all_songs(session=test_session)]
    assert sorted(remaining_song_ids) == sorted(ids_to_remain)

def test_db_delete_songs_empty_input(test_session):
    populate_test_db(test_session, num_songs=4)
    request = SongIdsRequest(song_ids=[])
    with pytest.raises(NotFoundError) as exc_info:
        db_delete_songs(request, test_session)
    assert exc_info.value.message == "Songs with such IDs were not found"

def test_db_delete_songs_non_existed_ids(test_session):
    populate_test_db(test_session, num_songs=4)
    request = SongIdsRequest(song_ids=[666, 999])
    with pytest.raises(NotFoundError) as exc_info:
        db_delete_songs(request, test_session)
    assert exc_info.value.message == "Songs with such IDs were not found"

def test_db_delete_songs_partially_existed_ids(test_session):
    """
    Ensure that when a mix of valid and invalid song IDs are passed,
    only the existing ones are deleted and the rest are ignored.
    """
    songs = populate_test_db(test_session, num_songs=4)
    non_existed_id = 999
    ids_for_delete = [songs[0].id, non_existed_id]
    expected_deleted_ids = [songs[0].id]
    expected_remaining_ids = [songs[1].id, songs[2].id, songs[3].id]

    request = SongIdsRequest(song_ids=ids_for_delete)
    deleted_songs = db_delete_songs(request, test_session)

    # Assert only the valid song ID was deleted
    assert sorted([song.id for song in deleted_songs]) == sorted(expected_deleted_ids)

    # Assert remaining songs are intact
    remaining_song_ids = [song.id for song in db_find_all_songs(session=test_session)]
    assert sorted(remaining_song_ids) == sorted(expected_remaining_ids)
