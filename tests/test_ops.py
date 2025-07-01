import pytest
from pydantic import ValidationError

from models.operations import (
    NotFoundError, SongDisplayMode, db_find_song, db_find_songs_by_id,
    db_find_all_songs, db_read_song, db_find_songs, db_create_song, db_edit_song, db_delete_songs, DISPLAY_MODES
)
from models.schemas import SongIdsRequest, SongCreate, SongUpdate
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
    assert [song.id for song in found] == [song.id for song in songs]

@pytest.mark.parametrize(
    "display",
    [
        SongDisplayMode.short,
        SongDisplayMode.full,
        SongDisplayMode.for_edit,
        SongDisplayMode.for_display,
    ],
    ids=["short", "full", "for_edit", "for_display"]
)
def test_db_read_song(display: SongDisplayMode, test_session):
    """This 4 tests basically test not only read song display, but read_songs display also (both use same function)"""
    songs = populate_test_db(test_session, num_songs=1)
    song = db_read_song(song_id=songs[0].id, session=test_session, display=display)
    assert song.id == songs[0].id
    assert song.title == songs[0].title
    assert song.artist.id == songs[0].artist.id
    assert isinstance(song, DISPLAY_MODES[display])
    if display == SongDisplayMode.full:
        assert len(song.lines) == len(songs[0].lines)
    elif display == SongDisplayMode.short:
        assert not hasattr(song, "lines")
        assert not hasattr(song, "lyrics")
    elif display == SongDisplayMode.for_edit:
        lyrics = ''
        for line in songs[0].lines:
            lyrics += f"({line.chords[0].name}){line.text[:5]}({line.chords[1].name}){line.text[5:]}\n"
        assert song.lyrics == lyrics
    elif display == SongDisplayMode.for_display:
        lyrics = ''
        for line in songs[0].lines:
            blanks = " " * (line.chords[1].position - len(line.chords[0].name))
            lyrics += f"{line.chords[0].name}{blanks}{line.chords[1].name} \n{line.text}\n"
        assert song.lyrics == lyrics

def test_db_find_songs(test_session):
    songs = populate_test_db(test_session, num_songs=3)
    found, _ = db_find_songs(skip=0, limit=100, search="", session=test_session)
    assert len(found) == len(songs)
    assert [song.id for song in found] == [song.id for song in songs]

@pytest.mark.parametrize(
    "search, expected_count, expected_field_name",
    [
        pytest.param(lambda songs: songs[0].title.split()[-1], 1, "title", id="search_by_title"),
        pytest.param(lambda songs: songs[0].artist.name.split()[-1], 1, "artist", id="search_by_artist"),
        pytest.param(lambda songs: songs[0].lines[0].text.split()[0], 1, "lines", id="search_by_lyrics"),
        pytest.param(lambda songs: "NotExistedString", 0, None, id="search_not_found"),
        pytest.param(lambda songs: songs[0].title.split()[-1].upper(), 1, "title", id="search_case_insensitive")
    ]
)
def test_db_find_songs_with_search(search, expected_count, expected_field_name, test_session):
    songs = populate_test_db(test_session, num_songs=3)
    search_term = search(songs)
    found, search_results = db_find_songs(skip=0, limit=100, search=search_term, session=test_session)

    if expected_field_name is not None:
        highlights = search_results[0]['highlight']

        assert found[0].id == songs[0].id

        field_assertion_msg = f"Expected highlight field '{expected_field_name}', got: {highlights}"
        assert expected_field_name in highlights, field_assertion_msg

        term_assertion_msg = f"Expected term '<em>{search_term}</em>' in highlights: {highlights}"
        expected_highlight = f"<em>{search_term}</em>".upper()
        actual_highlight = highlights[expected_field_name][0].upper()
        assert expected_highlight in actual_highlight, term_assertion_msg
    else:
        assert search_results == []

    assert len(found) == expected_count

def test_db_create_song(test_session):
    songs = populate_test_db(test_session, num_songs=1)
    song_in = SongCreate(
        title="Song Title",
        artist_id=songs[0].artist.id,
        lyrics="(Am)Song (Dm)Line 1\n(Am)Song (Dm)Line 2",
    )
    song = db_create_song(song_in, test_session)
    song_id = song.id
    created_song = db_find_song(song_id=song_id, session=test_session)
    assert created_song.title == "Song Title"
    assert created_song.artist.name == songs[0].artist.name
    assert len(created_song.lines) == 2

def test_db_create_song_with_empty_data(test_session):
    songs = populate_test_db(test_session, num_songs=1)
    with pytest.raises(ValidationError) as exc_info:
        SongCreate(title="", artist_id=songs[0].artist_id, lyrics="")

    errors = exc_info.value.errors()
    assert len(errors) == 2

    expected_fields = ["title", "lyrics"]
    for field in expected_fields:
        assert any(
            e["loc"] == (field,) and f"`{field}` must not be empty or blank" in e["msg"] for e in errors
        )

def test_db_edit_song_with_no_lyrics(test_session):
    songs = populate_test_db(test_session, num_songs=2)
    song_data = SongUpdate(title="New title", artist_id=songs[1].artist_id)
    db_edit_song(song_id=songs[0].id, song_data=song_data, session=test_session)

    created_song = db_find_song(song_id=songs[0].id, session=test_session)
    assert created_song.title == "New title"
    assert created_song.artist.name == songs[1].artist.name
    # Assert lyrics (lines) stayed the same
    assert [line.text for line in created_song.lines] == [line.text for line in songs[0].lines]

def test_db_edit_song_with_lyrics(test_session):
    songs = populate_test_db(test_session, num_songs=2)
    song_data = SongUpdate(title="New title", artist_id=songs[1].artist_id, lyrics="(Am)Song (Dm)Line 1\n(Am)Song (Dm)Line 2")
    db_edit_song(song_id=songs[0].id, song_data=song_data, session=test_session)

    created_song = db_find_song(song_id=songs[0].id, session=test_session)

    assert created_song.title == "New title"
    assert created_song.artist.name == songs[1].artist.name

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

@pytest.mark.parametrize(
    "id_selector, expected_deleted, expected_remaining, expect_error",
    [
        pytest.param(
            lambda songs: [songs[0].id, songs[1].id],
            lambda songs: [songs[0].id, songs[1].id],
            lambda songs: [songs[2].id, songs[3].id],
            False,
            id="delete_existing"
        ),
        pytest.param(
            lambda songs: [songs[0].id, 999],
            lambda songs: [songs[0].id],
            lambda songs: [songs[1].id, songs[2].id, songs[3].id],
            False,
            id="partially_existing"
        ),
        pytest.param(
            lambda songs: [666, 999],
            lambda songs: [],
            lambda songs: [song.id for song in songs],
            True,
            id="non_existent_ids"
        ),
        pytest.param(
            lambda songs: [],
            lambda songs: [],
            lambda songs: [song.id for song in songs],
            True,
            id="empty_input"
        ),
    ]
)
def test_db_delete_songs_all_cases(id_selector, expected_deleted, expected_remaining, expect_error, test_session):
    songs = populate_test_db(test_session, num_songs=4)
    ids_for_delete = id_selector(songs)

    if expect_error:
        with pytest.raises(NotFoundError) as exc_info:
            db_delete_songs(SongIdsRequest(song_ids=ids_for_delete), test_session)
            assert exc_info.value.message == "Songs with such IDs were not found"
    else:
        deleted_songs = db_delete_songs(SongIdsRequest(song_ids=ids_for_delete), test_session)
        deleted_ids = [song.id for song in deleted_songs]
        remaining_ids = [song.id for song in db_find_all_songs(session=test_session)]

        assert sorted(deleted_ids) == sorted(expected_deleted(songs))
        assert sorted(remaining_ids) == sorted(expected_remaining(songs))