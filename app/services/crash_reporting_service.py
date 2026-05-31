from __future__ import annotations

CRASH_SEVERITIES = ("fatal", "error", "warning")


class CrashReportingService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "capture_unhandled_exceptions": True,
            "include_stack_traces": True,
            "include_request_context": True,
            "retention_days": 90,
        }

    def capture_crash(
        self,
        *,
        error_type: str,
        message: str,
        stack_trace: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        return {
            "captured": True,
            "crash_id": f"crash-{error_type.lower()}",
            "error_type": error_type,
            "message": message,
            "stack_trace_included": stack_trace is not None,
            "trace_id": trace_id,
            "severity": "fatal" if error_type in ("RuntimeError", "SystemError") else "error",
        }

    def get_recent_crashes(self, *, limit: int = 10) -> dict:
        sample = [
            {
                "crash_id": "crash-sample-1",
                "error_type": "ValueError",
                "message": "Invalid input",
                "timestamp": "2026-05-29T08:00:00Z",
            }
        ]
        return {"crashes": sample[:limit], "total": len(sample)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "unhandled_capture": True,
            "stack_traces": True,
            "request_context": True,
        }
