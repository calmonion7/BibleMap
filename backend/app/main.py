from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import nodes, places, events

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(nodes.router)
app.include_router(places.router)
app.include_router(events.router)
