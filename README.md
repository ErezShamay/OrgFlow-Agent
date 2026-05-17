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

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload