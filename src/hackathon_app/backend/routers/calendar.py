from fastapi import APIRouter
from hackathon_app.backend.calendar.add_reminder_to_google_calender import add_reminder

router = APIRouter(prefix="/add_reminder")

@router.post("/")
def handle_calendar(data: dict):
    events = data.get("events")
    add_reminder(events)
    return {"status": "success"}
