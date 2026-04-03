from fastapi import APIRouter
from database import supabase

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("/job/{job_id}")
def get_candidates_by_job(job_id: str):
    result = supabase.table("applications")\
        .select("*, candidates(name, email)")\
        .eq("job_id", job_id)\
        .order("ai_score", desc=True)\
        .execute()

    strong = []
    moderate = []
    not_fit = []

    for app in result.data:
        candidate = {
            "application_id": app["id"],
            "name": app["candidates"]["name"],
            "email": app["candidates"]["email"],
            "score": app["ai_score"],
            "reasoning": app["ai_reasoning"],
            "fit_category": app["fit_category"],
            "stage": app["stage"]
        }
        if app["fit_category"] == "strong":
            strong.append(candidate)
        elif app["fit_category"] == "moderate":
            moderate.append(candidate)
        else:
            not_fit.append(candidate)

    return {
        "job_id": job_id,
        "total": len(result.data),
        "strong": strong,
        "moderate": moderate,
        "not_fit": not_fit
    }