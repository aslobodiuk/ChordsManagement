from sqlmodel import Session
from models.db_models import Song, Line, Chord


def populate_test_db(session: Session, num_songs: int = 1) -> list[Song]:
    """
    Populate the test database with mock songs, lines, and chords.

    Parameters
    ----------
    `session` : `Session`
        Active SQLModel session to write data to.

    `num_songs` : `int`
        Number of songs to generate (default is 1).

    Returns
    -------
    `list[Song]`
        List of created `Song` objects with lines and chords included.
    """
    songs = []

    for i in range(num_songs):
        song = Song(title=f"Test Song {i+1}", artist=f"Artist {i+1}")
        for j in range(3):  # 3 lines per song
            line = Line(text=f"Line {j+1} of song {i+1}", song=song)
            for k in range(2):  # 2 chords per line
                chord = Chord(position=k * 5, name=f"C{k+1}", line=line)
                line.chords.append(chord)
            song.lines.append(line)
        session.add(song)
        songs.append(song)

    session.commit()
    for song in songs:
        session.refresh(song)

    return songs