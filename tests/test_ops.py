from models.operations import db_find_song

def test_db_find_song(test_session):
    song = db_find_song(song_id=1, session=test_session)
    assert song.title == "Test Song"