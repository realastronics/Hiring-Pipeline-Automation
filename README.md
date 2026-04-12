# Hiring Pipeline Automation

AI-powered hiring tool for lean HR teams at startups and small organizations. Screen hundreds of resumes in seconds, send personalized outreach from your own Gmail, and book interviews directly on Google Calendar — all from one clean dashboard.

**Live demo:** [hiring-pipeline-automation.vercel.app](https://hiring-pipeline-automation.vercel.app)

> The app is currently in private beta with Google OAuth in test mode. To get access, **email parthsharma0206@gmail.com** with your Gmail address and I'll add you as a tester within 24 hours.
---

## How to Use

### 1. Sign in
Click **Sign in with Google**. One click, no configuration. The app uses OAuth so emails and calendar invites come from your actual Gmail account.

### 2. Create a role
From the dashboard, click **+ New Role**. Enter your company name (first time only) and the job title. Each role gets its own pipeline.

### 3. Screen resumes

**Option A — Manual upload:** Upload PDF resumes directly. Works instantly.

**Option B — Google Form:** If you're collecting applications via Google Form, paste the linked Sheet ID. The tool reads candidate names, emails, and resume links automatically. Setup instructions in the [Google Form Integration](#google-form-integration) section below.

The AI (Groq llama-3.3-70b) scores every candidate 0–100 and classifies them as Strong Fit, Moderate Fit, or Not Fit, with a one-line reasoning for each decision. All calls run concurrently so 20 resumes screen in the same time as 1.

### 4. Send outreach
On the Outreach page, choose who to invite for interviews — Strong Fit only, Strong + Moderate, or custom selection. Rejection emails go to the rest. All emails send from your Gmail via OAuth, no SMTP configuration needed.

### 5. Schedule interviews
Add your team's available slots (interviewer name, email, datetime). Click **Match & Book All** — the system matches each invited candidate to an available slot and creates Google Calendar events with attendees automatically.

The dashboard shows live pipeline stats for every active role: screened → strong → invited → scheduled.
---

## Google Form Integration

Create a Google Form with these fields:
- Full name (short answer)
- Primary email address (short answer)
- Link to resume (short answer — candidates upload to a shared Drive folder and paste the link)

Then:
1. Link the form to a Google Sheet
2. Share the Sheet with the service account email (provided on setup) eg: hiring-bot-hehe@secure-answer-492122-r3.iam.gserviceaccount.com
3. Share the Drive folder with the same service account email
4. Paste the Sheet ID into the tool when screening

The tool auto-detects column names — no hardcoding required.

---

## Technical Aspect

### Architecture

```
React (Vite)  ──────────────────────────────►  FastAPI (Python)
   Vercel                                          Render
                                                      │
                                          ┌───────────┼───────────┐
                                          │           │           │
                                       Supabase    Groq API   Google APIs
                                      (PostgreSQL)  (LLM)    (Gmail, Calendar,
                                                              Sheets, Drive)
```

### Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite | Fast dev, clean component model |
| Backend | FastAPI (Python) | Async support, auto-generated API docs, familiar Python ecosystem |
| Database | Supabase (PostgreSQL) | Hosted PostgreSQL with free tier, REST API out of the box |
| AI | Groq — llama-3.3-70b | Fastest inference available, generous free tier, structured JSON output |
| Auth | Google OAuth 2.0 | HR already has Google accounts, removes all credential setup |
| Email | Gmail API (OAuth) | Emails come from the HR's own Gmail — no SMTP, no app passwords |
| Calendar | Google Calendar API (OAuth) | Invites created in the HR's real calendar |
| Resume ingestion | Google Sheets + Drive API | Meets HR where they already are |

### Database Schema

```sql
companies        → name
jobs             → company_id, title, status
candidates       → name, email (unique)
applications     → job_id, candidate_id (unique pair), fit_category, 
                   ai_score, ai_reasoning, stage
interview_slots  → job_id, interviewer details, slot_datetime, is_booked
scheduled_interviews → application_id, slot_id, calendar_event_id
users            → email (unique), name, google_token (OAuth credentials)
```

The `unique_job_candidate` constraint on `applications` prevents duplicate screening results when the same candidate is re-screened for the same role.

### AI Screening Pipeline

Each resume goes through a single Groq API call with a structured prompt that returns JSON — score (0–100), strengths, gaps, recommendation, and one-sentence reasoning. All resume screenings for a batch fire concurrently using `asyncio.gather()`, reducing a 20-resume batch from ~60 seconds to ~5 seconds.

The scoring rubric is generic and role-agnostic — the AI evaluates fit against whatever JD text you paste in, so the same tool works for engineering, design, operations, or any other function.

### OAuth Flow

```
HR clicks "Sign in with Google"
    → Backend builds auth URL (no PKCE — server-side flow)
    → Google redirects to /auth/callback with code
    → Backend exchanges code for access + refresh tokens via direct POST
    → Tokens stored in Supabase users table (per HR email)
    → Frontend receives email param, stores in localStorage
    → All subsequent Gmail/Calendar API calls use stored OAuth credentials
```

Token refresh is handled automatically by the Google client library on expiry.

### Why No SMTP / Service Account for Email

Early versions used Gmail SMTP with app passwords and a Google service account for Calendar. This required HR to enable 2FA, generate app passwords, create a GCP service account, share their calendar, and configure 6 environment variables — too much friction for a non-technical user.

OAuth replaced all of this. HR signs in once, grants permissions, and the app handles everything using their own credentials. Zero manual configuration.

### Deployment

**Backend (Render):** Python web service, root directory `Backend`, build command `pip install -r requirements.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`. All secrets injected via Render environment variables.

**Frontend (Vercel):** Root directory `Frontend`, Vite preset auto-detected. Single environment variable `VITE_API_URL` pointing to the Render backend URL. All `API` constants in React files use `import.meta.env.VITE_API_URL || 'http://localhost:8000'` for local fallback.

**Known limitation:** Render free tier spins down after 15 minutes of inactivity. First request after inactivity has a ~50 second cold start. Acceptable for a beta, worth upgrading before any real company depends on it.

### Self-Hosting

```bash
# Backend
cd Backend
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd Frontend
npm install
npm run dev
```

Required environment variables in `Backend/.env`:

```
GROQ_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_SHEET_ID=
OAUTHLIB_INSECURE_TRANSPORT=1
```

Google Cloud setup: enable Gmail API, Google Calendar API, Google Sheets API, Google Drive API. Create OAuth 2.0 Web Application credentials with `http://localhost:8000/auth/callback` as redirect URI. Create a service account and download the JSON key (minified to one line for the env variable).

### Roadmap

- [ ] Applicant-facing upload dashboard — removes Google Form dependency entirely, candidates upload directly to Supabase Storage
- [ ] Async screening for Google Form ingestion (currently sequential due to Drive download bottleneck)
- [ ] Manual override UI — HR drags candidates between fit categories before outreach
- [ ] Google OAuth verification — removes the test-user limitation, opens to any Google account
- [ ] Post-interview feedback collection
- [ ] Multi-user company accounts with role-based access (HR manager vs recruiter)

---
