from fastapi import FastAPI
from hackathon_app.backend.routers import chat, minutes_events, calendar

def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(chat.router)
    app.include_router(minutes_events.router)
    app.include_router(calendar.router)

    return app