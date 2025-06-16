import tkinter as tk
from pathlib import Path
from tkinter.filedialog import asksaveasfilename, askopenfilename, askopenfilenames

from chords import create_song_pdf, get_song_from_string, get_songs_from_files
from pdf_utils import create_pdf_base, merge_pdf_files

SONGS_FILENAME = f"{Path.home()}/Documents/songs.pdf"

def save_file(window, text_edit):
    filepath = asksaveasfilename(filetypes=[("Text files", "*.txt")])

    if not filepath:
        return

    with open(filepath, "w") as f:
        f.write(text_edit.get("1.0", tk.END))
    window.title(f"Open file: {filepath}")

def open_file(window, text_edit):
    filepath = askopenfilename(filetypes=[("Text files", "*.txt")])

    if not filepath:
        return

    text_edit.delete("1.0", tk.END)
    with open(filepath, "r") as f:
        text_edit.insert("1.0", f.read())
    window.title(f"Open file: {filepath}")

def to_pdf(window, text_edit):
    text = text_edit.get("1.0", tk.END)
    pdf = create_pdf_base()
    tmp_file = create_song_pdf(pdf, [get_song_from_string(text),])
    merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)
    window.after(500, lambda: show_non_blocking_message(window))

def to_pdf_multiple(window):
    file_paths = askopenfilenames(
        title="Select text files",
        filetypes=[("Text files", "*.txt")]
    )
    songs = get_songs_from_files(filenames=list(file_paths))
    window.title(f"Open file: {file_paths}")
    pdf = create_pdf_base()
    tmp_file = create_song_pdf(pdf, songs)
    merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)
    window.after(500, lambda: show_non_blocking_message(window))

def show_non_blocking_message(window, msg="Success!", duration=2000):
    # Create a popup window
    popup = tk.Toplevel(window)
    popup.title("")
    popup.attributes("-topmost", True)
    popup.resizable(False, False)
    popup.overrideredirect(True)  # Hide window decorations

    # Set popup size
    width, height = 200, 60
    popup.geometry(f"{width}x{height}")

    # Calculate position: top-right of the root window
    window.update_idletasks()  # Ensure root window has correct size
    root_x = window.winfo_rootx()
    root_y = window.winfo_rooty()
    root_width = window.winfo_width()

    x = root_x + root_width - width - 10  # 10px padding from right
    y = root_y + 10  # 10px padding from top
    popup.geometry(f"+{x}+{y}")

    # Add message label
    label = tk.Label(popup, text=msg, font=("Arial", 11), bg="#dff0d8", fg="#3c763d", relief="solid", bd=1)
    label.pack(expand=True, fill="both", padx=10, pady=10)

    # Auto-destroy after duration (e.g., 2000 ms)
    popup.after(duration, popup.destroy)
