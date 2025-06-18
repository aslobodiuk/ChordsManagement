import tkinter as tk
from pathlib import Path
from tkinter.filedialog import asksaveasfilename, askopenfilename, askopenfilenames

from data_transformation import create_song_pdf, get_song_from_string, get_songs_from_files
from pdf_utils import create_pdf_base, merge_pdf_files

SONGS_FILENAME = f"{Path.home()}/Documents/songs.pdf"

class ChordEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x800")
        self.root.title("Chord Converter")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        self.frame = tk.Frame(root, relief="raised", bd=2)
        self.frame.grid(row=0, column=0, sticky="ns")

        save_button = tk.Button(self.frame, text="Save", command=self.save_file)
        open_button = tk.Button(self.frame, text="Open", command=self.open_file)
        to_pdf_button = tk.Button(self.frame, text="To PDF", command=self.to_pdf)
        dir_to_pdf = tk.Button(self.frame, text="To PDF (multiple)", command=self.to_pdf_multiple)

        save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        open_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        to_pdf_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        dir_to_pdf.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        self.text_edit = tk.Text(root, font=("Times", 18))
        self.text_edit.grid(row=0, column=1, sticky="nsew")
        self.text_edit.tag_configure("chord", foreground="red")
        self.text_edit.bind("<Button-2>", self.handle_click)

    def handle_click(self, event):
        def create_entry():
            index = self.text_edit.index(f"@{event.x},{event.y}")
            entry = tk.Entry(self.text_edit, font=("Times", 18), width=5, justify='center')
            entry.place(x=event.x-30, y=event.y-45)
            entry.focus_set()
            entry.bind("<Return>", lambda event: self.input_chord(event, index))
            print("You clicked at:", index)
        # Delay entry creation slightly so Text widget doesn't steal focus
        self.root.after(1, create_entry)

    def input_chord(self, event, index):
        self.text_edit.insert(index, f"({event.widget.get()})", "chord")
        event.widget.destroy()

    def save_file(self):
        filepath = asksaveasfilename(filetypes=[("Text files", "*.txt")])

        if not filepath:
            return

        with open(filepath, "w") as f:
            f.write(self.text_edit.get("1.0", tk.END))
        self.root.title(f"Open file: {filepath}")

    def open_file(self):
        filepath = askopenfilename(filetypes=[("Text files", "*.txt")])

        if not filepath:
            return

        self.text_edit.delete("1.0", tk.END)
        with open(filepath, "r") as f:
            self.text_edit.insert("1.0", f.read())
        self.root.title(f"Open file: {filepath}")

    def to_pdf(self):
        text = self.text_edit.get("1.0", tk.END)
        pdf = create_pdf_base()
        tmp_file = create_song_pdf(pdf, [get_song_from_string(text),])
        merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)
        self.root.after(500, self.show_non_blocking_message)

    def to_pdf_multiple(self):
        file_paths = askopenfilenames(
            title="Select text files",
            filetypes=[("Text files", "*.txt")]
        )
        songs = get_songs_from_files(filenames=list(file_paths))
        pdf = create_pdf_base()
        tmp_file = create_song_pdf(pdf, songs)
        merge_pdf_files(SONGS_FILENAME, tmp_file, SONGS_FILENAME)
        self.root.after(500, self.show_non_blocking_message)

    def show_non_blocking_message(self, msg: str = "Success!", duration: int = 2000) -> None:
        # Create a popup window
        popup = tk.Toplevel(self.root)
        popup.title("")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)
        popup.overrideredirect(True)  # Hide window decorations

        # Set popup size
        width, height = 200, 60
        popup.geometry(f"{width}x{height}")

        # Calculate position: top-right of the root window
        self.root.update_idletasks()  # Ensure root window has correct size
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()

        x = root_x + root_width - width - 10  # 10px padding from right
        y = root_y + 10  # 10px padding from top
        popup.geometry(f"+{x}+{y}")

        # Add message label
        label = tk.Label(popup, text=msg, font=("Arial", 11), bg="#dff0d8", fg="#3c763d", relief="solid", bd=1)
        label.pack(expand=True, fill="both", padx=10, pady=10)

        # Auto-destroy after duration (e.g., 2000 ms)
        popup.after(duration, popup.destroy)
