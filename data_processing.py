import re
from collections import defaultdict

from models import Song, Line, Chord

CHORDS_PATTERN = r"\(([A-G][#b]?(?:m|maj|min|dim|aug|sus|add)?\d*(?:/[A-G][#b]?)?)\)"

def convert_raw_data_into_song(title: str, artist: str, lyrics: str) -> Song:
    """
    :param title: song title
    :param artist: song artist
    :param lyrics: song lyrics with chords in brackets
    :return: Song object
    """
    song = Song(title=title, artist=artist)
    lines = lyrics.splitlines()
    for line in lines:
        line = Line(line=line.strip(), song=song)
        chords = defaultdict(str)
        matches = re.finditer(CHORDS_PATTERN, line.line)
        sub = 0  # we need subtractor for correct chord position in final line
        for match in matches:
            chord = match.group(1)  # chord without brackets
            start = match.start()
            end = match.end()
            chords[start - sub] = chord if not chords[start - sub] else f"{chords[start - sub]} {chord}"
            sub += end - start
        line.line = re.sub(CHORDS_PATTERN, "", line.line)
        for position, chord in chords.items():
            line.chords.append(Chord(position=position, chord=chord, line=line))
        song.lines.append(line)
    return song