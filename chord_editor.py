import re
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import asksaveasfilename, askopenfilename, askopenfilenames

from data_transformation import create_song_pdf, get_song_from_string, get_songs_from_files, CHORDS_PATTERN
from pdf_utils import create_pdf_base, merge_pdf_files

SONGS_FILENAME = f"{Path.home()}/Documents/songs.pdf"

class ChordEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x800")
        self.root.title("Chord Converter")

        self.button_mapper = {
            'save': ("Save", self.save_file),
            'open': ("Open", self.open_file),
            'to_pdf': ("To PFD", self.to_pdf),
            'to_pdf_multiple': ("To PDF (multiple)", self.to_pdf_multiple)
        }
        self.buttons = {}

        self._setup_widgets()
        self._configure_layout()
        self._bind_events()

    def _setup_widgets(self):
        # set up frame with buttons
        self.frame = tk.Frame(self.root, relief="raised", bd=2)
        self.frame.grid(row=0, column=0, sticky="ns")

        i = 0
        for k, v in self.button_mapper.items():
            self.buttons[k] = tk.Button(self.frame, text=v[0], command=v[1])
            self.buttons[k].grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            i += 1
        
        # set up text edit widget
        self.text_widget = tk.Text(self.root, font=("Times", 18))
        self.text_widget.grid(row=0, column=1, sticky="nsew")
        self.text_widget.tag_configure("chord", foreground="red")

    def _configure_layout(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

    def _bind_events(self):
        self.text_widget.bind("<Button-2>", self.on_text_widget_right_click)
        self.text_widget.bind("<<Paste>>", self.on_paste)

    def on_text_widget_right_click(self, event):
        def create_entry():
            index = self.text_widget.index(f"@{event.x},{event.y}")
            entry = tk.Entry(self.text_widget, font=("Times", 18), width=5, justify='center')
            entry.place(x=event.x, y=event.y - 45) # todo calculate this 45
            entry.focus_set()
            entry.bind("<Return>", lambda e: self.input_chord(e, index))
            entry.bind("<FocusOut>", lambda e: entry.destroy())
        # Delay entry creation slightly so Text widget doesn't steal focus
        self.root.after(1, create_entry)

    def on_paste(self, _):
        # Let Tkinter finish pasting (delay using after), then highlight
        self.text_widget.after(1, self.highlight_chords)

    def highlight_chords(self):
        self.text_widget.tag_remove("chord", "1.0", tk.END)  # Clear old tags
        lines = self.text_widget.get("1.0", tk.END).splitlines()
        for lineno, line in enumerate(lines, start=1):
            for match in re.finditer(CHORDS_PATTERN, line):
                start = f"{lineno}.{match.start()}"
                end = f"{lineno}.{match.end()}"
                self.text_widget.tag_add("chord", start, end)

    def input_chord(self, event, index):
        if event.widget.get():
            if re.fullmatch(CHORDS_PATTERN, f"({event.widget.get()})") is None:
                self.root.after(500, lambda: self.show_non_blocking_message(type='error', msg="Wrong input"))
            else:
                self.text_widget.insert(index, f"({event.widget.get()})", "chord")
        event.widget.destroy()

    def save_file(self):
        filepath = asksaveasfilename(filetypes=[("Text files", "*.txt")])

        if not filepath:
            return

        with open(filepath, "w") as f:
            f.write(self.text_widget.get("1.0", tk.END))

    def open_file(self):
        filepath = askopenfilename(
            title="Select text files",
            filetypes=[("Text files", "*.txt")]
        )

        if not filepath:
            return

        self.text_widget.delete("1.0", tk.END)
        with open(filepath, "r") as f:
            self.text_widget.insert("1.0", f.read())
            self.highlight_chords()

    def to_pdf(self):
        text = self.text_widget.get("1.0", tk.END)
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

    def show_non_blocking_message(self, type: str = 'success', msg: str = "Success", duration: int = 2000):
        style = {
            'success': ('#dff0d8', '#3c763d'),
            'error': ('#f2dede', '#a94442')
        }
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
        label = tk.Label(popup, text=msg, font=("Arial", 11), bg=style[type][0], fg=style[type][1], relief="solid", bd=1)
        label.pack(expand=True, fill="both", padx=10, pady=10)

        # Auto-destroy after duration (e.g., 2000 ms)
        popup.after(duration, popup.destroy)
