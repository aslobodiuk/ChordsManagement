import io
import re
from collections import defaultdict

from fpdf import FPDF

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

def convert_songs_to_pdf(pdf: FPDF, songs: list[Song]) -> io.BytesIO:
    """
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
                chords_line += blanks + chord.chord

            if not song.lines[i].line and not chords_line: # empty line
                pdf.cell(w=0, h=2 * cell_height, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(w=0, h=cell_height, text=chords_line, new_x="LMARGIN", new_y="NEXT")
                end_of_pure_chords_block = (
                        chords_line and
                        not song.lines[i].line and
                        i < len(song.lines) - 1 and
                        song.lines[i + 1].line
                )
                if song.lines[i].line or end_of_pure_chords_block:
                    pdf.cell(w=0, h=cell_height, text=song.lines[i].line, new_x="LMARGIN", new_y="NEXT")

    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)

    return pdf_bytes