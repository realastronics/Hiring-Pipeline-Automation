from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hiring Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Hiring Tool API is running"}

# sample run

from database import supabase

@app.get("/test-db")
def test_db():
    result = supabase.table("companies").select("*").execute()
    return {"status": "connected", "data": result.data}

# Make sure uvicorn is running, then open:
# http://localhost:8000/test-db