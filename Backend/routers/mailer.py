from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import supabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/email", tags=["Email"])

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ── Pydantic models ──────────────────────────────────────

class EmailTarget(BaseModel):
    application_id: str
    name: str
    email: str

class SendInviteRequest(BaseModel):
    targets: List[EmailTarget]
    form_link: str
    job_title: str

class SendRejectionRequest(BaseModel):
    targets: List[EmailTarget]
    job_title: str

# ── SMTP helper ──────────────────────────────────────────

def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed to {to_email}: {e}")
        return False

# ── Endpoints ────────────────────────────────────────────

@router.post("/invite")
def send_invites(req: SendInviteRequest):
    sent = []
    failed = []

    for target in req.targets:
        subject = f"Interview Invitation – {req.job_title}"
        body = f"""Dear {target.name},

Congratulations! You have been shortlisted for the {req.job_title} position.

Please share your availability using the link below — kindly respond within 48 hours:
{req.form_link}

We look forward to speaking with you.

Warm regards,
Talent Acquisition Team"""

        success = send_email(target.email, subject, body)

        if success:
            supabase.table("applications").update(
                {"stage": "invited"}
            ).eq("id", target.application_id).execute()
            sent.append(target.name)
        else:
            failed.append(target.name)

    return {"sent": sent, "failed": failed}


@router.post("/reject")
def send_rejections(req: SendRejectionRequest):
    sent = []
    failed = []

    for target in req.targets:
        subject = f"Your Application – {req.job_title}"
        body = f"""Dear {target.name},

Thank you for taking the time to apply for the {req.job_title} position.

After carefully reviewing your application, we will not be moving forward with your candidacy at this time. This was a competitive process and we received many strong applications.

We appreciate your interest and encourage you to apply for future opportunities.

We wish you all the best.

Warm regards,
Talent Acquisition Team"""

        success = send_email(target.email, subject, body)

        if success:
            supabase.table("applications").update(
                {"stage": "rejected"}
            ).eq("id", target.application_id).execute()
            sent.append(target.name)
        else:
            failed.append(target.name)

    return {"sent": sent, "failed": failed}