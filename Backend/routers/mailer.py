from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import base64
import os
from email.mime.text import MIMEText
from database import supabase
from dotenv import load_dotenv
from pathlib import Path
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/email", tags=["Email"])

def send_email_oauth(to_email: str, subject: str, body: str, user_email: str) -> bool:
    try:
        from routers.auth import get_user_credentials
        creds = get_user_credentials(user_email)
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(body, "plain")
        message["To"] = to_email
        message["Subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()
        return True
    except Exception as e:
        print(f"OAuth email failed to {to_email}: {e}")
        return False

class EmailTarget(BaseModel):
    application_id: str
    name: str
    email: str

class SendInviteRequest(BaseModel):
    targets: List[EmailTarget]
    form_link: str
    job_title: str
    user_email: str

class SendRejectionRequest(BaseModel):
    targets: List[EmailTarget]
    job_title: str
    user_email: str

@router.post("/invite")
def send_invites(req: SendInviteRequest):
    sent = []
    failed = []

    for target in req.targets:
        subject = f"Interview Invitation – {req.job_title}"
        body = f"""Dear {target.name},

Congratulations! We are pleased to inform you that you have been shortlisted for the interview round of the {req.job_title} position.

Please share your availability using the link below — kindly respond within 48 hours:
{req.form_link}

We look forward to speaking with you.

Warm regards,
Talent Acquisition Team"""

        success = send_email_oauth(target.email, subject, body, req.user_email)

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

        success = send_email_oauth(target.email, subject, body, req.user_email)

        if success:
            supabase.table("applications").update(
                {"stage": "rejected"}
            ).eq("id", target.application_id).execute()
            sent.append(target.name)
        else:
            failed.append(target.name)

    return {"sent": sent, "failed": failed}