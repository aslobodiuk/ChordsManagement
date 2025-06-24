import os

import uvicorn
from fastapi import FastAPI

from api.routes import router

PROTOCOL = os.getenv("PROTOCOL")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Chord Editor API")
app.include_router(router)

# Function to run the FastAPI server
def run_server():
    uvicorn.run(app, host=HOST, port=PORT)