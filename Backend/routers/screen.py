from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import PyPDF2
import tempfile
import os
import json
import io
from groq import Groq
from database import supabase
from dotenv import load_dotenv
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials as SACredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/screen", tags=["Screening"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Helpers ──────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        text = ""
        with open(tmp_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        os.unlink(tmp_path)
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def screen_resume(candidate_name: str, resume_text: str, jd_text: str) -> dict:
    system_prompt = """You are an expert HR screening assistant.
Evaluate the resume against the job description and return ONLY valid JSON:
{
  "score": <0-100>,
  "strengths": ["s1", "s2", "s3"],
  "gaps": ["g1", "g2"],
  "recommendation": "Strong Fit | Moderate Fit | Not Fit",
  "reasoning": "one sentence summary"
}
Strong Fit >= 70 | Moderate Fit 40-69 | Not Fit < 40"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"JD:\n{jd_text}\n\nCandidate: {candidate_name}\n\nResume:\n{resume_text}"}
            ],
            temperature=0.2,
            max_tokens=600
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"Groq error for {candidate_name}: {e}")
        return {
            "score": 0,
            "strengths": [],
            "gaps": ["Could not evaluate"],
            "recommendation": "Not Fit",
            "reasoning": "Screening error occurred."
        }


def get_google_creds():
    sa_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    return SACredentials.from_service_account_info(
        sa_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )


def parse_file_id(resume_url: str) -> str | None:
    if "/d/" in resume_url:
        return resume_url.split("/d/")[1].split("/")[0]
    elif "id=" in resume_url:
        return resume_url.split("id=")[1].split("&")[0]
    return None


def download_from_drive(file_id: str, creds) -> bytes:
    drive_service = build("drive", "v3", credentials=creds)
    request = drive_service.files().get_media(fileId=file_id)
    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return file_buffer.getvalue()


def save_to_db(candidate_name: str, candidate_email: str, job_id: str, ai_result: dict) -> dict:
    fit_map = {
        "Strong Fit": "strong",
        "Moderate Fit": "moderate",
        "Not Fit": "not_fit"
    }

    candidate = supabase.table("candidates").upsert({
        "name": candidate_name,
        "email": candidate_email
    }, on_conflict="email").execute()

    candidate_id = candidate.data[0]["id"]

    application = supabase.table("applications").insert({
        "job_id": job_id,
        "candidate_id": candidate_id,
        "fit_category": fit_map.get(ai_result["recommendation"], "not_fit"),
        "ai_score": ai_result["score"],
        "ai_reasoning": ai_result["reasoning"],
        "stage": "screened"
    }).execute()

    return application.data[0]


# ── Endpoints ─────────────────────────────────────────────

@router.post("/")
async def screen_resumes(
    job_id: str = Form(...),
    jd_text: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    results = []

    for resume_file in resumes:
        file_bytes = await resume_file.read()
        resume_text = extract_text_from_pdf(file_bytes)

        if not resume_text:
            print(f"Could not extract text from {resume_file.filename}")
            continue

        candidate_name = resume_file.filename.replace(".pdf", "").replace("_", " ").title()
        candidate_email = f"pending_{candidate_name.replace(' ', '_').lower()}@placeholder.com"

        ai_result = screen_resume(candidate_name, resume_text, jd_text)
        application = save_to_db(candidate_name, candidate_email, job_id, ai_result)

        results.append({
            "candidate_name": candidate_name,
            "application_id": application["id"],
            **ai_result
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {"job_id": job_id, "total": len(results), "results": results}


@router.post("/from-sheet")
async def screen_from_sheet(job_id: str = Form(...), jd_text: str = Form(...)):
    creds = get_google_creds()
    gc = gspread.authorize(creds)

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sheet = gc.open_by_key(sheet_id).sheet1
    rows = sheet.get_all_records()

    print(f"Total rows found: {len(rows)}")

    results = []

    for row in rows:
        candidate_name = row.get("Your full name", "").strip()
        candidate_email = row.get("Primary Email Address", "").strip()
        resume_url = row.get("Resume", "").strip()

        if not candidate_name or not candidate_email or not resume_url:
            print(f"Skipping incomplete row: {row}")
            continue

        file_id = parse_file_id(resume_url)
        if not file_id:
            print(f"Cannot parse Drive URL for {candidate_name}: {resume_url}")
            continue

        print(f"Processing {candidate_name} — file_id: {file_id}")

        try:
            file_bytes = download_from_drive(file_id, creds)
        except Exception as e:
            print(f"Drive download failed for {candidate_name}: {e}")
            continue

        resume_text = extract_text_from_pdf(file_bytes)

        if not resume_text:
            print(f"Empty resume text for {candidate_name}")
            continue

        ai_result = screen_resume(candidate_name, resume_text, jd_text)
        application = save_to_db(candidate_name, candidate_email, job_id, ai_result)

        results.append({
            "candidate_name": candidate_name,
            "application_id": application["id"],
            **ai_result
        })

        print(f"Done: {candidate_name} — {ai_result['recommendation']}")

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {"job_id": job_id, "total": len(results), "results": results}