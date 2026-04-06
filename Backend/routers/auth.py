from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from database import supabase
from dotenv import load_dotenv
from pathlib import Path
import os
import json
import requests as req

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

router = APIRouter(prefix="/auth", tags=["Auth"])

CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = None
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"

SCOPES = " ".join([
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events"
])

def get_env():
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI")
    }


@router.get("/login")
def login():
    env = get_env()
    # Build auth URL manually — no PKCE, no Flow object
    auth_url = (
        f"{AUTH_URI}"
        f"?client_id={env['client_id']}"
        f"&redirect_uri={env['redirect_uri']}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse("http://localhost:5173/login?error=no_code")

    env = get_env()

    try:
        # Exchange code for token manually — no Flow, no PKCE
        token_response = req.post(TOKEN_URI, data={
            "code": code,
            "client_id": env["client_id"],
            "client_secret": env["client_secret"],
            "redirect_uri": env["redirect_uri"],
            "grant_type": "authorization_code"
        })

        token_data = token_response.json()
        print(f"Token response: {token_data}")

        if "error" in token_data:
            print(f"Token error: {token_data}")
            return RedirectResponse("http://localhost:5173/login?error=token_failed")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # Get user info
        user_response = req.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_response.json()
        print(f"User info: {user_info}")

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            return RedirectResponse("http://localhost:5173/login?error=no_email")

        stored_token = {
            "token": access_token,
            "refresh_token": refresh_token,
            "token_uri": TOKEN_URI,
            "client_id": env["client_id"],
            "client_secret": env["client_secret"],
            "scopes": SCOPES.split()
        }

        supabase.table("users").upsert({
            "email": email,
            "name": name,
            "google_token": json.dumps(stored_token)
        }, on_conflict="email").execute()

        return RedirectResponse(f"http://localhost:5173/dashboard?user={email}")

    except Exception as e:
        print(f"Auth callback error: {e}")
        return RedirectResponse("http://localhost:5173/login?error=auth_failed")


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
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )