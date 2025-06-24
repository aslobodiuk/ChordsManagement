import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from tkinter.filedialog import asksaveasfilename, askopenfilename, askopenfilenames

import requests

from data_transformation import create_song_pdf, get_song_from_string, get_songs_from_files, CHORDS_PATTERN
from server import HOST, PORT, PROTOCOL
from utils.pdf_utils import create_pdf_base, merge_pdf_files

SONGS_FILENAME = f"{Path.home()}/Documents/songs.pdf"

def run_gui():
    app = ChordEditor()
    app.mainloop()


class ChordEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.url = f"{PROTOCOL}://{HOST}:{PORT}"
        self.song_id_map = {}
        self.selected_song_ids = []
        self.current_song_id = None

        self.title("Chord Editor: New song")
        self.geometry("900x600")

        self.configure_grid()
        self.create_library_section()
        self.create_editor_section()
        self.create_action_buttons()

    def configure_grid(self):
        self.columnconfigure(0, weight=1, minsize=300)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

    def create_library_section(self):
        library_frame = ttk.LabelFrame(self, text="Library")
        library_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.song_listbox = tk.Listbox(library_frame, selectmode=tk.EXTENDED)
        self.song_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.refresh_song_library()

        self.song_listbox.bind("<<ListboxSelect>>", self.on_song_select)
        self.song_listbox.bind("<Double-Button-1>", self.on_song_double_click)

        delete_button = ttk.Button(self, text="Delete selected", command=self.delete_selected_songs)
        delete_button.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

    def create_editor_section(self):
        editor_frame = ttk.Frame(self)
        editor_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(2, weight=1)

        # Title and artist
        ttk.Label(editor_frame, text="Title:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(editor_frame)
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=(50, 0))

        ttk.Label(editor_frame, text="Artist:").grid(row=1, column=0, sticky="w")
        self.artist_entry = ttk.Entry(editor_frame)
        self.artist_entry.grid(row=1, column=0, sticky="ew", padx=(50, 0))

        # Lyrics text area
        self.lyrics_text = tk.Text(editor_frame, wrap=tk.WORD)
        self.lyrics_text.grid(row=2, column=0, sticky="nsew", pady=5)

    def create_action_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 5))

        for i in range(3):
            button_frame.columnconfigure(i, weight=1)

        export_button = ttk.Button(
            button_frame,
            text="Export selected to PDF",
            command=lambda: self.export_to_pdf(self.selected_song_ids)
        )
        export_button.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        save_button = ttk.Button(
            button_frame,
            text="Save/Update",
            command=self.save_song
        )
        save_button.grid(row=0, column=1, sticky="ew", padx=2)

        new_button = ttk.Button(
            button_frame,
            text="New Song",
            command=self.clear_editor
        )
        new_button.grid(row=0, column=2, sticky="ew", padx=(2, 0))

    def on_song_select(self, event):
        selection = self.song_listbox.curselection()
        self.selected_song_ids = [self.song_id_map[i] for i in selection]
        print(f"Selected IDs: {self.selected_song_ids}")

    def on_song_double_click(self, event):
        selection = self.song_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        song_id = self.song_id_map.get(index)
        if not song_id:
            return

        try:
            # Fetch song details from API
            response = requests.get(f"{self.url}/songs/{song_id}", params={'display': 'for_edit'})
            response.raise_for_status()
            data = response.json()

            # Populate editor fields
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, data["title"])

            self.artist_entry.delete(0, tk.END)
            self.artist_entry.insert(0, data["artist"])

            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", data["lyrics"])

            # Store song ID for future updates
            self.current_song_id = song_id

            self.title(f"Chord Editor: {data['title']} - {data['artist']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load song details:\n{e}")

    def export_to_pdf(self, selected_song_ids):
        try:
            response = requests.post(
                f"{self.url}/songs/to_pdf",
                json={"song_ids": selected_song_ids},
                stream=True
            )

            if response.status_code != 200:
                raise Exception(f"Failed to generate PDF: {response.status_code}")

            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save PDF as..."
            )

            if not file_path:
                return  # User canceled

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            messagebox.showinfo("Success", f"PDF saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_song(self):
        title = self.title_entry.get().strip()
        artist = self.artist_entry.get().strip()
        lyrics = self.lyrics_text.get("1.0", tk.END).strip()

        if not title or not artist or not lyrics:
            messagebox.showwarning("Missing Data", "Title, artist, and lyrics must not be empty.")
            return

        payload = {
            "title": title,
            "artist": artist,
            "lyrics": lyrics
        }

        try:
            if self.current_song_id is None:
                # Create song
                response = requests.post(f"{self.url}/songs", json=payload)
                response.raise_for_status()
                messagebox.showinfo("Success", "Song created successfully.")
            else:
                # Update song
                response = requests.put(f"{self.url}/songs/{self.current_song_id}", json=payload)
                response.raise_for_status()
                messagebox.showinfo("Success", "Song updated successfully.")
            self.title(f"Chord Editor: {payload['title']} - {payload['artist']}")

            # Refresh library
            self.refresh_song_library()
            self.clear_editor()

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to save song:\n{e}")

    def delete_selected_songs(self):
        if not self.selected_song_ids:
            messagebox.showinfo("No selection", "Please select at least one song to delete.")
            return

        confirm = messagebox.askyesno(
            title="Confirm Deletion",
            message=f"Are you sure you want to delete {len(self.selected_song_ids)} song(s)?"
        )
        if not confirm:
            return

        try:
            response = requests.delete(
                f"{self.url}/songs",
                json={"song_ids": self.selected_song_ids}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", "Selected songs deleted.")
            self.refresh_song_library()
            self.clear_editor()

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to delete songs:\n{e}")

    def clear_editor(self):
        self.title("Chord Editor: New song")
        self.current_song_id = None
        self.title_entry.delete(0, tk.END)
        self.artist_entry.delete(0, tk.END)
        self.lyrics_text.delete("1.0", tk.END)

    def refresh_song_library(self):
        try:
            response = requests.get(f"{self.url}/songs", params={'display': 'short'})
            response.raise_for_status()
            response.raise_for_status()
            songs = response.json()

            self.song_listbox.delete(0, tk.END)
            self.song_id_map.clear()

            for i, song in enumerate(songs):
                self.song_listbox.insert(tk.END, f"{song['title']} - {song['artist']}")
                self.song_id_map[i] = song["id"]

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to refresh library:\n{e}")


class ChordEditor_legacy:
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
                self.root.after(500, lambda: self.show_non_blocking_message(msg_type='error', msg="Wrong input"))
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

    def show_non_blocking_message(self, msg_type: str = 'success', msg: str = "Success", duration: int = 2000):
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
        label = tk.Label(popup, text=msg, font=("Arial", 11), bg=style[msg_type][0], fg=style[msg_type][1], relief="solid", bd=1)
        label.pack(expand=True, fill="both", padx=10, pady=10)

        # Auto-destroy after duration (e.g., 2000 ms)
        popup.after(duration, popup.destroy)
