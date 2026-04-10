# Hiring Pipeline Automation

AI-powered hiring tool for lean HR teams. Screen resumes, rank candidates, send interview invites, and schedule interviews — all from one dashboard.

Built with FastAPI, React, Supabase, and Groq LLM.
---

## What It Does

1. **Resume Screening** — Upload PDFs manually or pull _directly from a Google Form_. Groq LLM ranks candidates into Strong Fit, Moderate Fit, and Not Fit with a reasoning snippet per candidate.
2. **Candidate Outreach** — Send shortlisting and rejection emails directly from your Gmail account via OAuth — no SMTP setup.
3. **Interview Scheduling** — Add interviewer availability slots, match candidates, and book Google Calendar events automatically.
4. **Multi-role Dashboard** — Manage multiple open positions simultaneously with live pipeline stats per role.
---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| AI | Groq API — llama-3.3-70b |
| Auth | Google OAuth 2.0 |
| Email | Gmail API (OAuth) |
| Calendar | Google Calendar API |
| Resume ingestion | Google Sheets + Drive API |
---

## Local Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- A Supabase project
- A Google Cloud project with OAuth credentials

### 1. Clone and install

```bash
git clone https://github.com/realastronics/hiring-pipeline
cd hiring-pipeline
```

Activating Backend:
```bash
cd Backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Activating Frontend:
```bash
cd Frontend
npm install
```

### 2. Environment variables

Create `Backend/.env`:
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEET_ID=your_responses_sheet_id
SMTP_USER=your_gmail
SMTP_PASSWORD=your_app_password
OAUTHLIB_INSECURE_TRANSPORT=1

### 3. Database setup

Run in Supabase SQL Editor:

```sql
CREATE TABLE companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE candidates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    resume_file_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    candidate_id UUID REFERENCES candidates(id),
    fit_category TEXT CHECK (fit_category IN ('strong', 'moderate', 'not_fit')),
    ai_score INTEGER,
    ai_reasoning TEXT,
    stage TEXT DEFAULT 'screened',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE interview_slots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    interviewer_name TEXT NOT NULL,
    interviewer_email TEXT NOT NULL,
    slot_datetime TIMESTAMP NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scheduled_interviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    slot_id UUID REFERENCES interview_slots(id),
    calendar_event_id TEXT,
    confirmation_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    google_token TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Google Cloud setup

1. Create a project at console.cloud.google.com
2. Enable: Gmail API, Google Calendar API, Google Sheets API, Google Drive API
3. Create OAuth 2.0 credentials → Web application
   - Authorized redirect URI: `http://localhost:8000/auth/callback`
4. Create a Service Account → download JSON key
5. Add your Gmail as a test user under OAuth consent screen → Audience

### 5. Run

Terminal 1 — Backend:
```bash
cd Backend
$env:OAUTHLIB_INSECURE_TRANSPORT = "1"  # Windows PowerShell
& "C:\Envs\hiring-pipeline\Scripts\Activate.ps1"
uvicorn main:app --reload
```

Terminal 2 — Frontend:
```bash
cd Frontend
npm run dev
```

Open `http://localhost:5173`
---

## Google Form Integration

To use the "From Google Form" screening mode:

1. Create a Google Form with these fields:
   - Email (short answer)
   - Full name (short answer)
   - Primary email address (short answer)
   - Link to resume (short answer — candidates paste a Google Drive link)
2. Link the form to a Google Sheet
3. Share the Google Sheet with your service account email (`your-bot@your-project.iam.gserviceaccount.com`)
4. Create a shared Google Drive folder → share with the same service account email → instruct candidates to upload their resume PDF here and paste the sharing link into the form
5. Paste the Sheet ID into the tool

The Sheet ID is the long string in the URL: `docs.google.com/spreadsheets/d/**SHEET_ID**/edit`
---

## Deploying to Production

### Backend → Render
1. Push to GitHub
2. Create a new Web Service on Render → connect repo → set root to `Backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add all `.env` variables in Render's Environment tab
6. Set `GOOGLE_REDIRECT_URI` to `https://your-render-url.onrender.com/auth/callback`

### Frontend → Vercel
1. Create new project on Vercel → connect repo → set root to `Frontend`
2. Set `VITE_API_URL` environment variable to your Render backend URL
3. Update `API` constant in all frontend files to use `import.meta.env.VITE_API_URL`

### Google OAuth for Production
- Add your production redirect URI in Google Cloud Console
- Submit for OAuth verification to allow users outside your test list
- You will need a privacy policy URL — create a simple one at `/privacy` in your frontend

---

## Known Limitations

- Google OAuth is currently in test mode — add users manually at console.cloud.google.com → Audience → Test users (up to 100)
- Resume text extraction works best with text-based PDFs — scanned image PDFs will return empty text
- Groq free tier has rate limits — for batches above 30 resumes, add delays between API calls
- Calendar booking requires the HR's Google Calendar to be shared with the service account, or OAuth credentials with calendar scope

---
