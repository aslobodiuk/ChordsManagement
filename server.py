import os

import uvicorn
from fastapi import FastAPI, Response

from api.routes import router
from settings import settings

PROTOCOL = os.getenv("PROTOCOL")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Chord Editor API")
app.include_router(router)

# Function to run the FastAPI server
def run_server():
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=True)

@app.get("/", include_in_schema=False)
def root():
    """Health check"""
    return Response("Server is running!", status_code=200)