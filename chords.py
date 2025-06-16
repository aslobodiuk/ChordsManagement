import re
from collections import defaultdict
from dataclasses import dataclass

from fpdf import FPDF


@dataclass
class Line:
    line: str
    chords: dict[int, str]

@dataclass
class Song:
    title: str
    artist: str
    lines: list[Line]

def convert_input_files_into_songs(filenames: list[str]) -> list[Song]:
    """
    :param filenames: list of txt files. Format:
        title
        artist
        song text - song lines with chords in brackets:
                (Bm)Help! I need some(Bm/A)body, (G)help! Not just anybody,\n(E7)Help! You know I need someone, (A)help!
    :return: list of Song objects
    """
    chords_pattern = r"\(([A-G][#b]?(?:m|maj|min|dim|aug|sus|add)?\d*(?:/[A-G][#b]?)?)\)"
    songs = []
    for filename in filenames:
        result_lines = list()
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            title = lines[0].strip()
            artist = lines[1].strip()
            for line in lines[2:]:
                line = line.strip()
                chords = defaultdict(str)
                matches = re.finditer(chords_pattern, line)
                sub = 0 # we need subtractor for correct chord position in final line
                for match in matches:
                    chord = match.group(1)  # chord without brackets
                    start = match.start()
                    end = match.end()
                    chords[start - sub] = chord if not chords[start - sub] else f"{chords[start - sub]} {chord}"
                    sub += end - start
                line = re.sub(chords_pattern, "", line)
                result_lines.append(Line(line, chords))
            songs.append(Song(title, artist, result_lines))
    return songs

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
        """
        v1
        for line in song.lines:
            cell_height = 3
            if pdf.get_y() + 2 * cell_height > pdf.h - pdf.b_margin:
                pdf.add_page()
            chords_line = convert_line_chords_to_string(line)
            if not line.line and not chords_line:
                pdf.cell(w=0, h=2 * cell_height, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(w=0, h=cell_height, text=chords_line, new_x="LMARGIN", new_y="NEXT")
                if line.line:
                    pdf.cell(w=0, h=cell_height, text=line.line, new_x="LMARGIN", new_y="NEXT")
        """

    # Save overlay to file
    overlay_path = "overlay.pdf"
    pdf.output(overlay_path)
    return overlay_path
