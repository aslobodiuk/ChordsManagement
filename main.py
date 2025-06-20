import threading

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from gui.chord_editor import run_gui
from db import engine
from models import Line, Song, Chord
from server import run_server


def main() -> None:
    # get_song_with_lines_and_chords(1)
    # create_sample_song()

    # Start FastAPI server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    run_gui()

def create_sample_song():
    with Session(engine) as session:
        # Create a new song
        song = Song(title="Let It Be", artist="The Beatles")

        # Create 3 lines
        for i in range(1, 4):
            line_text = f"This is line {i}"
            line = Line(line=line_text, song=song)

            # Add two chords to each line (position 0 and 5)
            chord1 = Chord(position=0, chord="Am", line=line)
            chord2 = Chord(position=5, chord="G", line=line)

            line.chords.extend([chord1, chord2])
            song.lines.append(line)

        session.add(song)
        session.commit()
        session.refresh(song)

        print(f"Song created with ID: {song.id}")

def get_song_with_lines_and_chords(song_id: int):
    with Session(engine) as session:
        statement = (
            select(Song)
            .where(Song.id == song_id)
            .options(
                selectinload(Song.lines).selectinload(Line.chords)
            )
        )

        result = session.exec(statement).first()

        if not result:
            print("Song not found")
            return

        print(f"🎵 Song: {result.title} by {result.artist}")
        for line in result.lines:
            print(f"  ➤ Line: {line.line}")
            for chord in line.chords:
                print(f"     🎶 Chord at {chord.position}: {chord.chord}")

if __name__ == "__main__":
    main()