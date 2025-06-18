import re
from collections import defaultdict
from dataclasses import dataclass

from fpdf import FPDF

CHORDS_PATTERN = r"\(([A-G][#b]?(?:m|maj|min|dim|aug|sus|add)?\d*(?:/[A-G][#b]?)?)\)"

@dataclass
class Line:
    line: str
    chords: dict[int, str]

@dataclass
class Song:
    title: str
    artist: str
    lines: list[Line]

def convert_raw_data_into_song(title: str, artist: str, lines: list[str]) -> Song:
    """
    :param title: song title
    :param artist: song artist
    :param lines: list of song lines with chords in brackets
    :return: Song object
    """
    result_lines = list()
    for line in lines:
        line = line.strip()
        chords = defaultdict(str)
        matches = re.finditer(CHORDS_PATTERN, line)
        sub = 0  # we need subtractor for correct chord position in final line
        for match in matches:
            chord = match.group(1)  # chord without brackets
            start = match.start()
            end = match.end()
            chords[start - sub] = chord if not chords[start - sub] else f"{chords[start - sub]} {chord}"
            sub += end - start
        line = re.sub(CHORDS_PATTERN, "", line)
        result_lines.append(Line(line, chords))
    return Song(title, artist, result_lines)

def get_songs_from_files(filenames: list[str]) -> list[Song]:
    """
    :param filenames: list of filenames(*.txt). Format:
        title
        artist
        song text - song lines with chords in brackets:
                (Bm)Help! I need some(Bm/A)body, (G)help! Not just anybody,\n(E7)Help! You know I need someone, (A)help!
    :return: list of Song objects
    """
    songs = []
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            song = convert_raw_data_into_song(
                title=lines[0].strip(),
                artist=lines[1].strip(),
                lines=lines[2:]
            )
            songs.append(song)
    return songs

def get_song_from_string(input_string: str) -> Song:
    """
    :param input_string: string with specific format:
        title
        artist
        song text - song lines with chords in brackets:
                (Bm)Help! I need some(Bm/A)body, (G)help! Not just anybody,\n(E7)Help! You know I need someone, (A)help!
    :return: Song object
    """
    lines = input_string.splitlines()
    song = convert_raw_data_into_song(
        title=lines[0].strip(),
        artist=lines[1].strip(),
        lines=lines[2:]
    )
    return song

def convert_line_chords_to_string(line: Line) -> str:
    """
    :param line: song line with chords
    :return: string of chords with necessary blanks
    """
    result = ''
    for position, chord in line.chords.items():
        blanks = ' ' * (position - len(result))
        if not blanks and result:
            blanks = ' '
        result += blanks + chord
    return result

def create_song_pdf(pdf: FPDF, songs: list[Song]) -> str:
    """
    :param pdf: FPDF object
    :param songs: list of Song objects
    :return: creates pdf file with formatting, returns filename
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
            chords_line = convert_line_chords_to_string(song.lines[i])
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

    tmp_path = "tmp.pdf"
    pdf.output(tmp_path)
    return tmp_path
