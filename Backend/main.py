from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import screen

app = FastAPI(title="Hiring Tool API")
app.include_router(screen.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Hiring Tool API is running"}