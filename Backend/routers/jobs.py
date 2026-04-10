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

@router.get("/{job_id}/stats")
def get_job_stats(job_id: str):
    result = supabase.table("applications")\
        .select("fit_category, stage")\
        .eq("job_id", job_id)\
        .execute()
    
    data = result.data
    return {
        "total": len(data),
        "strong": sum(1 for r in data if r["fit_category"] == "strong"),
        "moderate": sum(1 for r in data if r["fit_category"] == "moderate"),
        "not_fit": sum(1 for r in data if r["fit_category"] == "not_fit"),
        "invited": sum(1 for r in data if r["stage"] == "invited"),
        "scheduled": sum(1 for r in data if r["stage"] == "scheduled")
    }

@router.get("/company/{company_id}")
def get_jobs_by_company(company_id: str):
    result = supabase.table("jobs")\
        .select("*")\
        .eq("company_id", company_id)\
        .eq("status", "active")\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@router.delete("/{job_id}/clear")
def clear_job_screening(job_id: str):
    # Delete scheduled interviews first (foreign key constraint)
    app_ids = supabase.table("applications")\
        .select("id")\
        .eq("job_id", job_id)\
        .execute()
    
    ids = [a["id"] for a in app_ids.data]
    
    if ids:
        supabase.table("scheduled_interviews")\
            .delete()\
            .in_("application_id", ids)\
            .execute()
        
        supabase.table("applications")\
            .delete()\
            .eq("job_id", job_id)\
            .execute()

    return {"cleared": len(ids)}