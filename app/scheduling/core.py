"""Single shared BackgroundScheduler instance for the whole backend.

Previously app/automation/scheduler.py and app/jobs/scheduler.py each
instantiated their own BackgroundScheduler() - two independent schedulers.
Only one of them ever got started via `scheduler.start()` in the app
lifecycle, so jobs registered on the other one (QC notification jobs)
were silently never run. This module is now the one place the scheduler
is created; both app/automation/scheduler.py and app/jobs/scheduler.py
re-export it for backwards compatibility with existing imports.
"""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
