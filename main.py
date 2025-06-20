import threading

from gui.chord_editor import run_gui
from server import run_server


def main() -> None:
    # Start FastAPI server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Run tkinter app
    run_gui()

if __name__ == "__main__":
    main()