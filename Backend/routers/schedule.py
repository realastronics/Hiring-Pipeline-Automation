from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from database import supabase
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/schedule", tags=["Scheduling"])

class SlotInput(BaseModel):
    interviewer_name: str
    interviewer_email: str
    slot_datetime: str

class AddSlotsRequest(BaseModel):
    job_id: str
    slots: List[SlotInput]

class BookInterviewsRequest(BaseModel):
    job_id: str
    user_email: str

@router.post("/slots")
def add_interviewer_slots(req: AddSlotsRequest):
    rows = []
    for slot in req.slots:
        rows.append({
            "job_id": req.job_id,
            "interviewer_name": slot.interviewer_name,
            "interviewer_email": slot.interviewer_email,
            "slot_datetime": slot.slot_datetime,
            "is_booked": False
        })
    result = supabase.table("interview_slots").insert(rows).execute()
    return {"added": len(result.data), "slots": result.data}


@router.post("/match")
def match_and_book(req: BookInterviewsRequest):
    from routers.auth import get_user_credentials
    
    applications = supabase.table("applications")\
        .select("*, candidates(name, email)")\
        .eq("job_id", req.job_id)\
        .eq("stage", "invited")\
        .execute()

    slots = supabase.table("interview_slots")\
        .select("*")\
        .eq("job_id", req.job_id)\
        .eq("is_booked", False)\
        .execute()

    if not slots.data:
        return {"error": "No available slots — add interviewer slots first"}

    if not applications.data:
        return {"error": "No invited candidates — send invites first"}

    try:
        creds = get_user_credentials(req.user_email)
        calendar = build("calendar", "v3", credentials=creds)
    except Exception as e:
        return {"error": f"Calendar auth failed: {e}"}

    booked = []
    failed = []
    slot_index = 0

    for app in applications.data:
        if slot_index >= len(slots.data):
            failed.append(app["candidates"]["name"])
            continue

        slot = slots.data[slot_index]
        candidate_name = app["candidates"]["name"]
        candidate_email = app["candidates"]["email"]

        start_dt = datetime.fromisoformat(slot["slot_datetime"])
        end_dt = start_dt + timedelta(hours=1)

        event = {
            "summary": f"Interview – {candidate_name}",
            "description": f"Interview for {app['job_id']}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [
                {"email": candidate_email},
                {"email": slot["interviewer_email"]}
            ]
        }

        try:
            created = calendar.events().insert(
                calendarId="primary",
                body=event,
                sendUpdates="all"
            ).execute()

            supabase.table("interview_slots")\
                .update({"is_booked": True})\
                .eq("id", slot["id"])\
                .execute()

            supabase.table("scheduled_interviews").insert({
                "application_id": app["id"],
                "slot_id": slot["id"],
                "calendar_event_id": created["id"],
                "confirmation_sent": True
            }).execute()

            supabase.table("applications")\
                .update({"stage": "scheduled"})\
                .eq("id", app["id"])\
                .execute()

            booked.append({
                "candidate": candidate_name,
                "slot": slot["slot_datetime"],
                "interviewer": slot["interviewer_name"],
                "calendar_link": created.get("htmlLink")
            })
            slot_index += 1

        except Exception as e:
            failed.append(candidate_name)
            print(f"Calendar error for {candidate_name}: {e}")

    return {"booked": booked, "failed": failed}


@router.get("/job/{job_id}")
def get_schedule(job_id: str):
    result = supabase.table("scheduled_interviews")\
        .select("*, applications(stage, candidates(name, email)), interview_slots(slot_datetime, interviewer_name)")\
        .eq("applications.job_id", job_id)\
        .execute()
    return {"schedule": result.data}