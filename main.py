import argparse
from pathlib import Path

from chords import convert_input_files_into_songs, create_song_pdf
from pdf_utils import create_pdf_base, merge_pdf_files

DATA_DIR = "input_data"
SONGS_FILENAME = f"{Path.home()}/Documents/songs.pdf"

def main() -> None:
    parser = argparse.ArgumentParser(description="Process multiple txt files.")
    parser.add_argument(
        "filenames",  # Positional argument
        nargs="+",  # One or more values
        help="List of input filenames"
    )
    args = parser.parse_args()

    for filename in args.filenames:
        print(f"Processing: {filename}")

    songs =convert_input_files_into_songs(filenames=[f"{DATA_DIR}/{filename}" for filename in args.filenames])

    for song in songs:
        print("Title: ", song.title)
        print("Artist: ", song.artist)

    pdf = create_pdf_base()
    tmp_file = create_song_pdf(pdf, songs)
    merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)

if __name__ == "__main__":
    main()