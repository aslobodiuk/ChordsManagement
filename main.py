import tkinter as tk

from chord_editor import ChordEditor

def main() -> None:
    root = tk.Tk()
    ChordEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()