from fastapi import FastAPI
from hackathon_app.backend.routers import chat, minutes_events, room, user, calendar, rooms

def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(chat.router)
    app.include_router(minutes_events.router)
    app.include_router(calendar.router)
    app.include_router(rooms.router)
    app.include_router(room.router)
    app.include_router(user.router)

    return app
