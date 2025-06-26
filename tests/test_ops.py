from models.operations import db_find_song
from tests.utils import populate_test_db


def test_db_find_song(test_session):
    populate_test_db(test_session, num_songs=2)
    song = db_find_song(song_id=1, session=test_session)
    assert song.title == "Test Song 1"