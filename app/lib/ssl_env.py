from __future__ import annotations

import os


def sanitize_ssl_env() -> None:
    """Drop SSL cert env vars that point to missing files.

    httpx honors SSL_CERT_FILE / REQUESTS_CA_BUNDLE when trust_env=True and
    crashes at import time if the path does not exist.
    """
    for env_var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(env_var)
        if path and not os.path.isfile(path):
            os.environ.pop(env_var, None)
