from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import mailer
from routers import screen, candidates, mailer, schedule, jobs, auth
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")

app = FastAPI(title="Hiring Tool API")
app.include_router(screen.router)
app.include_router(candidates.router)
app.include_router(mailer.router)
app.include_router(schedule.router)
app.include_router(jobs.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],    
)

@app.get("/")
def root():
    return {"status": "Hiring Tool API is running"}