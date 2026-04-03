from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import PyPDF2
import tempfile
import os
import json
from groq import Groq
from database import supabase
from dotenv import load_dotenv
from pathlib import Path
import gspread 
from google.oauth2.service_account import Credentials as SACredentials

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/screen", tags=["Screening"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@router.post("/from-sheet")
async def screen_from_sheet(job_id: str = Form(...), jd_text: str = Form(...)):
    sa_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = SACredentials.from_service_account_info(
        sa_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    gc = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sheet = gc.open_by_key(sheet_id).sheet1
    rows = sheet.get_all_records()

    results = []
    for row in rows:
        candidate_name = row.get("Full Name", "").strip()
        candidate_email = row.get("Email", "").strip()
        resume_url = row.get("Resume", "").strip()

        if not candidate_name or not candidate_email:
            continue

        # Download resume from Drive
        file_id = resume_url.split("/d/")[1].split("/")[0]
        import requests as req
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        headers = {"Authorization": f"Bearer {creds.token}"}
        response = req.get(download_url, headers=headers)
        resume_text = extract_text_from_pdf(response.content)

        ai_result = screen_resume(candidate_name, resume_text, jd_text)

        fit_map = {"Strong Fit": "strong", "Moderate Fit": "moderate", "Not Fit": "not_fit"}

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

        results.append({
            "candidate_name": candidate_name,
            "application_id": application.data[0]["id"],
            **ai_result
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {"job_id": job_id, "total": len(results), "results": results}

def extract_text_from_pdf(file_bytes: bytes) -> str:
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
        candidate_name = resume_file.filename.replace(".pdf", "").replace("_", " ").title()

        ai_result = screen_resume(candidate_name, resume_text, jd_text)

        fit_map = {
            "Strong Fit": "strong",
            "Moderate Fit": "moderate", 
            "Not Fit": "not_fit"
        }

        # Save candidate to DB
        candidate = supabase.table("candidates").upsert({
            "name": candidate_name,
            "email": f"pending_{candidate_name.replace(' ', '_')}@placeholder.com"
        }, on_conflict="email").execute()

        candidate_id = candidate.data[0]["id"]

        # Save application to DB
        application = supabase.table("applications").insert({
            "job_id": job_id,
            "candidate_id": candidate_id,
            "fit_category": fit_map.get(ai_result["recommendation"], "not_fit"),
            "ai_score": ai_result["score"],
            "ai_reasoning": ai_result["reasoning"],
            "stage": "screened"
        }).execute()

        results.append({
            "candidate_name": candidate_name,
            "application_id": application.data[0]["id"],
            **ai_result
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {"job_id": job_id, "total": len(results), "results": results}