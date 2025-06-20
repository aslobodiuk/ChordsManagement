import uvicorn
from fastapi import FastAPI

from api.routes import router

app = FastAPI(title="Chord Editor API")
app.include_router(router)

# Function to run the FastAPI server
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)