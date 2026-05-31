from __future__ import annotations

TRACE_HEADERS = [
    "X-Trace-ID",
    "X-Request-ID",
    "traceparent",
    "tracestate",
]

SPAN_ATTRIBUTES = [
    "trace_id",
    "span_id",
    "parent_span_id",
    "service_name",
    "operation",
    "duration_ms",
]


class DistributedTracingService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "propagation": "w3c_tracecontext",
            "headers": TRACE_HEADERS,
            "sample_rate": 1.0,
            "backend": "structured_logs",
        }

    def create_span_context(
        self,
        *,
        trace_id: str,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> dict:
        return {
            "trace_id": trace_id,
            "span_id": span_id or "span-root",
            "parent_span_id": parent_span_id,
            "attributes": SPAN_ATTRIBUTES,
        }

    def validate_trace_headers(self, headers: dict) -> dict:
        present = [h for h in TRACE_HEADERS if h.lower() in {k.lower() for k in headers}]
        return {
            "valid": len(present) >= 1,
            "present_headers": present,
            "trace_id": headers.get("X-Trace-ID") or headers.get("x-trace-id"),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "headers_configured": len(TRACE_HEADERS) >= 2,
            "span_attributes": len(SPAN_ATTRIBUTES) >= 5,
            "middleware_compatible": True,
        }
