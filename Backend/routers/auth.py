from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from database import supabase
from dotenv import load_dotenv
from pathlib import Path
import os
import json

load_dotenv(Path(__file__).parent.parent / ".env")

router = APIRouter(prefix="/auth", tags=["Auth"])

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events"
]

def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")]
            }
        },
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )


@router.get("/login")
def login():
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code returned from Google"}

    flow = get_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Get user info
    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()

    email = user_info.get("email")
    name = user_info.get("name")

    # Store token in Supabase
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else []
    }

    # Upsert user into a users table
    supabase.table("users").upsert({
        "email": email,
        "name": name,
        "google_token": json.dumps(token_data)
    }, on_conflict="email").execute()

    # Redirect to frontend with email as param
    frontend_url = f"http://localhost:5173/dashboard?user={email}"
    return RedirectResponse(frontend_url)


@router.get("/me")
def get_user(email: str):
    result = supabase.table("users").select("*").eq("email", email).execute()
    if not result.data:
        return {"error": "User not found"}
    user = result.data[0]
    return {"email": user["email"], "name": user["name"]}


def get_user_credentials(email: str) -> Credentials:
    result = supabase.table("users").select("google_token").eq("email", email).execute()
    if not result.data:
        raise Exception(f"No credentials found for {email}")
    
    token_data = json.loads(result.data[0]["google_token"])
    
    return Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )