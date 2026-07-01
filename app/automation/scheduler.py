"""Backwards-compatible re-export.

The actual BackgroundScheduler instance now lives in
app/scheduling/core.py (shared with app/jobs/scheduler.py, which used to
own a second, independent instance - see that module's docstring history
/ app/scheduling/core.py for why that was a bug). Existing imports of
`from app.automation.scheduler import scheduler` keep working unchanged.
"""
from __future__ import annotations

from app.scheduling.core import scheduler

__all__ = ["scheduler"]
