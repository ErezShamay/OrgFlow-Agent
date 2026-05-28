from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime, timedelta
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings


WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Caches successful write responses by idempotency key."""

    def __init__(self, app):
        super().__init__(app)
        self._records: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS)
        self._header_name = settings.IDEMPOTENCY_HEADER

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method.upper() not in WRITE_METHODS:
            return await call_next(request)

        raw_key = request.headers.get(self._header_name)
        if not raw_key:
            return await call_next(request)

        idempotency_key = raw_key.strip()
        if not idempotency_key:
            return await call_next(request)

        body_bytes = await request.body()
        fingerprint = self._fingerprint(request, body_bytes)

        with self._lock:
            self._purge_expired_locked()
            existing = self._records.get(idempotency_key)
            if existing:
                if existing["fingerprint"] != fingerprint:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "success": False,
                            "error": {
                                "code": "IDEMPOTENCY_KEY_REUSED",
                                "message": "Idempotency key was already used for a different request payload",
                                "status_code": 409,
                            },
                        },
                    )
                replay = Response(
                    content=existing["body"],
                    status_code=existing["status_code"],
                    media_type=existing["media_type"],
                )
                replay.headers["X-Idempotency-Replayed"] = "true"
                return replay

        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        wrapped_response = Response(
            content=response_body,
            status_code=response.status_code,
            media_type=response.media_type,
            headers=dict(response.headers),
        )

        if 200 <= wrapped_response.status_code < 300:
            with self._lock:
                self._records[idempotency_key] = {
                    "fingerprint": fingerprint,
                    "status_code": wrapped_response.status_code,
                    "media_type": wrapped_response.media_type,
                    "body": response_body,
                    "expires_at": datetime.now(UTC) + self._ttl,
                }

        return wrapped_response

    def _purge_expired_locked(self) -> None:
        now = datetime.now(UTC)
        expired = [key for key, value in self._records.items() if value["expires_at"] <= now]
        for key in expired:
            self._records.pop(key, None)

    @staticmethod
    def _fingerprint(request: Request, body: bytes) -> str:
        payload = {
            "method": request.method.upper(),
            "path": request.url.path,
            "query": sorted(request.query_params.multi_items()),
            "body_sha256": hashlib.sha256(body).hexdigest(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
