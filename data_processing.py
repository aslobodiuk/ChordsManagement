import io
import re

from fpdf import FPDF
from sqlalchemy import Sequence

from models.db_models import Song, Line, Chord

CHORDS_PATTERN = r"\(([A-G][#b]?(?:m|maj|min|dim|aug|sus|add)?\d*(?:/[A-G][#b]?)?)\)"

def convert_lyrics_into_song_lines(lyrics: str, title: str = None, artist: str = None, song: Song = None) -> Song:
    """
    Parse lyrics with chords and convert them into a structured `Song` object
    with nested `Line` and `Chord` instances.
    :param lyrics: song lyrics with chords in brackets
    :param title: song title [optional]
    :param artist: song artist [optional]
    :param song: song object [optional]
    :return: Song object
    """
    if not song:
        song = Song(title=title, artist=artist)
    lines = lyrics.splitlines()
    for line in lines:
        line = Line(text=line.strip(), song=song)
        chords = dict()
        matches = re.finditer(CHORDS_PATTERN, line.text)
        sub = 0  # we need subtractor for correct chord position in final line
        for match in matches:
            chord = match.group(1)  # chord without brackets
            start = match.start()
            end = match.end()
            max_position = max(chords.keys()) + 1 if chords.keys() else 0
            chords[max(max_position, start - sub)] = chord
            sub += end - start
        line.text = re.sub(CHORDS_PATTERN, "", line.text)
        for position, name in chords.items():
            line.chords.append(Chord(position=position, name=name, line=line))
        song.lines.append(line)
    return song

def convert_song_lines_into_raw_lyrics(lines: list[Line]) -> str:
    """
    Convert structured `Line` and `Chord` objects back into raw lyrics
    format with chords inside brackets.
    :param lines: list of Line objects
    :return: song lyrics with chords in brackets
    """
    result = ""
    for line in lines:
        add = 0 # we need to add length of already used chords to keep correct chord position
        for chord in line.chords:
            line.text = f"{line.text[:chord.position + add]}({chord.name}){line.text[chord.position + add:]}"
            add += len(chord.name) + 2 # for ( and ) symbols
        result += line.text + '\n'
    return result

def convert_song_lines_into_formatted_lyrics(lines: list[Line]) -> str:
    """
    Convert structured lines into formatted lyrics with chords rendered above the words.
    Suitable for monospaced font rendering.
    :param lines: list of Line objects
    :return: formatted song lyrics with chords above words (suitable for monoscopic fonts)
    """
    result = ""
    for line in lines:
        chords_line = ''
        for chord in line.chords:
            blanks = ' ' * (chord.position - len(chords_line))
            chords_line += blanks + chord.name + ' '
        result += chords_line + '\n'
        result += line.text + '\n'

    return result

def convert_songs_to_pdf(pdf: FPDF, songs: Sequence[Song]) -> io.BytesIO:
    """
    Render a list of `Song` objects into a structured PDF format using `FPDF`.
    :param pdf: FPDF object
    :param songs: list of Song objects
    :return: stream of generated PDF file
    """
    for song in songs:
        pdf.add_page()
        # add title
        pdf.set_font("UbuntuMono", size=16, style="B")
        pdf.cell(w=0, h=10, text=song.title, new_x="LMARGIN", new_y="NEXT", align="C")
        # add artist
        pdf.set_font("UbuntuMono", size=12, style="I")
        pdf.cell(w=0, h=10, text=song.artist, new_x="LMARGIN", new_y="NEXT", align="R")
        # add song
        pdf.set_font("UbuntuMono", size=8)
        for i in range(len(song.lines)):
            cell_height = 3
            if pdf.get_y() + 2 * cell_height > pdf.h - pdf.b_margin:
                pdf.add_page()

            chords_line = ''
            for chord in song.lines[i].chords:
                blanks = ' ' * (chord.position - len(chords_line))
                if not blanks and chords_line:
                    blanks = ' '
                chords_line += blanks + chord.name

            if not song.lines[i].text and not chords_line: # empty line
                pdf.cell(w=0, h=2 * cell_height, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(w=0, h=cell_height, text=chords_line, new_x="LMARGIN", new_y="NEXT")
                end_of_pure_chords_block = (
                        chords_line and
                        not song.lines[i].text and
                        i < len(song.lines) - 1 and
                        song.lines[i + 1].text
                )
                if song.lines[i].text or end_of_pure_chords_block:
                    pdf.cell(w=0, h=cell_height, text=song.lines[i].text, new_x="LMARGIN", new_y="NEXT")

    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)

    return pdf_bytes