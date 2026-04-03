from fastapi import APIRouter
from pydantic import BaseModel
from database import supabase

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class CompanyCreate(BaseModel):
    name: str

class JobCreate(BaseModel):
    company_id: str
    title: str

@router.post("/company")
def create_company(req: CompanyCreate):
    result = supabase.table("companies").insert({"name": req.name}).execute()
    return result.data[0]

@router.post("/")
def create_job(req: JobCreate):
    result = supabase.table("jobs").insert({
        "company_id": req.company_id,
        "title": req.title,
        "status": "active"
    }).execute()
    return result.data[0]

@router.get("/{job_id}")
def get_job(job_id: str):
    result = supabase.table("jobs").select("*").eq("id", job_id).execute()
    return result.data[0]