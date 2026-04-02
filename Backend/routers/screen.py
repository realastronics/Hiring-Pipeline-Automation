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

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/screen", tags=["Screening"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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