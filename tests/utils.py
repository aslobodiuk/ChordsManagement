from sqlmodel import Session, select

from elasticsearch_client import index_song, es
from models.db_models import Song, Line, Chord, Artist
from settings import get_settings

settings = get_settings()


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

    titles_pool = [
        "Morning Sunrise",
        "Night Dance",
        "Whispered Calls",
        "Mountain Echoes",
        "Endless Rivers",
        "Starry Skies",
        "Flight of Dreams",
        "Fading Shadows",
        "Heartbeat",
        "Forever Yours"
    ]

    artists_pool = [
        "The Luminaries",
        "Midnight Wanderers",
        "Echoes of Silence",
        "The Mountain Folk",
        "River Flow",
        "Starlight Ensemble",
        "Dreamcatchers",
        "Shadow Players",
        "Heartbeat Band",
        "Forever Crew"
    ]

    lyrics_pool = [
        "Sunshine in the morning",
        "Dancing through the night",
        "Whispering winds call my name",
        "Mountains echo your voice",
        "Rivers flow endlessly",
        "Stars light the dark sky",
        "Dreams take flight tonight",
        "Shadows fade away",
        "Hearts beat as one",
        "Forever in your arms"
    ]

    chord_names = ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]

    for i in range(num_songs):
        title = titles_pool[i % len(titles_pool)]
        artist_name = artists_pool[i % len(artists_pool)]
        artist = session.exec(select(Artist).where(Artist.name == artist_name)).first()
        if artist is None:
            artist = Artist(name=artist_name)

        song = Song(title=title, artist=artist)

        for j in range(3):  # 3 lines per song
            line_text = lyrics_pool[(i * 3 + j) % len(lyrics_pool)]
            line = Line(text=line_text, song=song)

            for k in range(2):  # 2 chords per line
                chord_name = chord_names[(i * 3 * 2 + j * 2 + k) % len(chord_names)]
                chord = Chord(position=k * 5, name=chord_name, line=line)
                line.chords.append(chord)
            song.lines.append(line)

        session.add(song)
        songs.append(song)

    session.commit()
    for song in songs:
        session.refresh(song)
        index_song(song)
    es.indices.refresh(index=settings.ES_INDEX_NAME)

    return songs
