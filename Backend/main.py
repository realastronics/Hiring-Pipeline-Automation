from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.routers import mailer
from routers import screen
from routers import screen, candidates
from routers import screen, candidates
from routers import screen, candidates, schedule

app = FastAPI(title="Hiring Tool API")
app.include_router(screen.router)
app.include_router(screen.router)
app.include_router(candidates.router)
app.include_router(screen.router)
app.include_router(candidates.router)
app.include_router(mailer.router)
app.include_router(screen.router)
app.include_router(candidates.router)
app.include_router(mailer.router)
app.include_router(schedule.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],    
)

@app.get("/")
def root():
    return {"status": "Hiring Tool API is running"}