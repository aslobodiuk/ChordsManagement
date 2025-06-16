import argparse
import tkinter as tk

from chords import get_songs_from_files, create_song_pdf
from pdf_utils import create_pdf_base, merge_pdf_files
from tkinter_utils import save_file, open_file, to_pdf, SONGS_FILENAME

DATA_DIR = "input_data"

def main_legacy() -> None:
    parser = argparse.ArgumentParser(description="Process multiple txt files.")
    parser.add_argument(
        "filenames",  # Positional argument
        nargs="+",  # One or more values
        help="List of input filenames"
    )
    args = parser.parse_args()

    for filename in args.filenames:
        print(f"Processing: {filename}")

    songs =get_songs_from_files(filenames=[f"{DATA_DIR}/{filename}" for filename in args.filenames])

    for song in songs:
        print("Title: ", song.title)
        print("Artist: ", song.artist)

    pdf = create_pdf_base()
    tmp_file = create_song_pdf(pdf, songs)
    merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)

def main() -> None:
    window = tk.Tk()
    window.geometry("1200x800")
    window.title("Chord Converter")
    window.rowconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)

    text_edit = tk.Text(window)
    text_edit.grid(row=0, column=1, sticky="nsew")

    frame = tk.Frame(window, relief="raised", bd=2)

    save_button = tk.Button(frame, text="Save", command=lambda: save_file(window, text_edit))
    open_button = tk.Button(frame, text="Open", command=lambda: open_file(window, text_edit))
    to_pdf_button = tk.Button(frame, text="To PDF", command=lambda: to_pdf(window, text_edit))

    save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    open_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    to_pdf_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    frame.grid(row=0, column=0, sticky="ns")

    window.mainloop()

if __name__ == "__main__":
    main()