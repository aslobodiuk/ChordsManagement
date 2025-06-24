import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import requests

from data_processing import CHORDS_PATTERN
from server import HOST, PORT, PROTOCOL

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

        self.lyrics_text.bind("<Button-2>", self.on_lyrics_right_click)
        self.lyrics_text.bind("<<Paste>>", self.on_lyrics_paste)
        self.lyrics_text.tag_configure("chord", foreground="red")

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

            # Let Tkinter finish pasting (delay using after), then highlight
            self.lyrics_text.after(1, self.highlight_chords)

            # Store song ID for future updates
            self.current_song_id = song_id

            self.title(f"Chord Editor: {data['title']} - {data['artist']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load song details:\n{e}")

    def on_lyrics_right_click(self, event):
        def create_entry():
            index = self.lyrics_text.index(f"@{event.x},{event.y}")
            entry = tk.Entry(self.lyrics_text, font=("Times", 18), width=5, justify='center')
            entry.place(x=event.x, y=event.y)
            entry.focus_set()
            entry.bind("<Return>", lambda e: self.input_chord(e, index))
            entry.bind("<FocusOut>", lambda e: entry.destroy())
        # Delay entry creation slightly so Text widget doesn't steal focus
        self.after(1, create_entry)

    def on_lyrics_paste(self, _):
        # Let Tkinter finish pasting (delay using after), then highlight
        self.lyrics_text.after(1, self.highlight_chords)

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

    def highlight_chords(self):
        self.lyrics_text.tag_remove("chord", "1.0", tk.END)  # Clear old tags
        lines = self.lyrics_text.get("1.0", tk.END).splitlines()
        for lineno, line in enumerate(lines, start=1):
            for match in re.finditer(CHORDS_PATTERN, line):
                start = f"{lineno}.{match.start()}"
                end = f"{lineno}.{match.end()}"
                self.lyrics_text.tag_add("chord", start, end)

    def input_chord(self, event, index):
        if event.widget.get():
            if re.fullmatch(CHORDS_PATTERN, f"({event.widget.get()})") is None:
                self.after(500, lambda: messagebox.showerror("Error", f"Wrong input"))
            else:
                self.lyrics_text.insert(index, f"({event.widget.get()})", "chord")
        event.widget.destroy()
