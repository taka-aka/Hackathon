from fastapi import FastAPI
from hackathon_app.backend.routers import chat, minutes_events, calendar, rooms, room

def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(chat.router)
    app.include_router(minutes_events.router)
    app.include_router(calendar.router)
    app.include_router(rooms.router)
    app.include_router(room.router)

    return app
