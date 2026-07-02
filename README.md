# ElayoAI (OrgFlow Agent)

One Stop Shop לניהול פרויקט בנייה — FastAPI + Next.js.

## מסמכי מקור

| מסמך | תפקיד |
|------|--------|
| [`docs/PRODUCT-SPEC-LOCKED.md`](docs/PRODUCT-SPEC-LOCKED.md) | מוצר נעול (מה/למה) |
| [`docs/FIELD-REPORT-FINALIZE-PIPELINE.md`](docs/FIELD-REPORT-FINALIZE-PIPELINE.md) | מימוש Finalize + PROGRESS (F1–F8 הושלם) |
| [`docs/COMPETITIVE-LAYER-SPEC.md`](docs/COMPETITIVE-LAYER-SPEC.md) | שכבת תחרות v2 — חזון (Zero Setup, V/X, Instant Loop) |
| [`docs/COMPETITIVE-LAYER-TASKS.md`](docs/COMPETITIVE-LAYER-TASKS.md) | **משימות לסוכן** — Z/V/L/R gates + PROGRESS |
| [`docs/FIELD-REPORT-CHECKLISTS.md`](docs/FIELD-REPORT-CHECKLISTS.md) | צ'קליסטים |
| [`docs/HANDOFF-AGENT-PROMPT.md`](docs/HANDOFF-AGENT-PROMPT.md) | handoff לסוכן |
| [`docs/PILOT-CHECKLIST.md`](docs/PILOT-CHECKLIST.md) | פיילוט שטח |
| [`docs/PROJECT-SUPERVISION-DASHBOARD-SPEC.md`](docs/PROJECT-SUPERVISION-DASHBOARD-SPEC.md) | דשבורד פרויקט למפקח — מפרט מוצר (זרימה, UI, חישוב ג) |
| [`docs/PROJECT-SUPERVISION-DASHBOARD-TASKS.md`](docs/PROJECT-SUPERVISION-DASHBOARD-TASKS.md) | **משימות לסוכן** — gates D1–D10 + PROGRESS |

## Run locally

Requires **Python 3.12** (matches CI). On Windows, install via `winget install Python.Python.3.12`.

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -c constraints.txt
uvicorn app.main:app --reload
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -c constraints.txt
uvicorn app.main:app --reload
```

If `py` is unavailable, use the full path:
`$env:LOCALAPPDATA\Programs\Python\Python312\python.exe`

## Frontend development

```bash
cd orgflow-ui
npm ci
npm run dev
```

In `orgflow-ui/.env.local` you can control the auth behavior for local development:

- `NEXT_PUBLIC_API_URL` should point to the backend, e.g. `http://127.0.0.1:8000`
- `NEXT_PUBLIC_FORCE_LOGIN=false` - in the browser, auth is stored per tab (`sessionStorage`) and ends when the tab is closed; reopening the app shows the public home page until you sign in again
- `NEXT_PUBLIC_FORCE_LOGIN=true` forces sign-out on every page load (including refresh), for stricter local testing
