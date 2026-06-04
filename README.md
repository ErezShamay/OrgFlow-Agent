# OrgFlow Agent

Internal organizational workflow agent MVP.

## Current capabilities

- Intent detection
- Entity extraction
- Planner
- Step executor
- Workflow history
- Human confirmation flow
- Rule-based + LLM mock fallback
- Optional OpenAI adapter
- FastAPI endpoints
- Pytest coverage

## Deploy to cloud (preview, ~$0/month)

See [docs/deploy-preview-cloud.md](docs/deploy-preview-cloud.md) — Vercel (UI) + Render (API) + Supabase (DB).

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend development

In `orgflow-ui/.env.local` you can control the auth behavior for local development:

- `NEXT_PUBLIC_API_URL` should point to the backend, e.g. `http://127.0.0.1:8000`
- `NEXT_PUBLIC_FORCE_LOGIN=false` means existing sessions will be respected
- `NEXT_PUBLIC_FORCE_LOGIN=true` forces the app to sign out any session and show the login page on startup
