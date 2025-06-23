import threading

from pydantic.v1 import BaseSettings

from gui.chord_editor import run_gui
from server import run_server

class Settings(BaseSettings):
    RUN_GUI: bool = False

    class Config:
        env_file = ".env"

def main() -> None:
    settings = Settings()

    if settings.RUN_GUI:
        # Start FastAPI server in a thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Run tkinter app
        run_gui()

    run_server()

if __name__ == "__main__":
    main()