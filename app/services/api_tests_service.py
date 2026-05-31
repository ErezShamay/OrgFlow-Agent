from __future__ import annotations

API_TEST_CONFIG = {
    "client": "fastapi_testclient",
    "auth_fixture": "jwt_bearer",
    "base_path": "/",
    "assert_status_codes": True,
}


class ApiTestsService:
    def get_config(self) -> dict:
        return API_TEST_CONFIG

    def list_endpoints(self) -> dict:
        endpoints = [
            {"method": "GET", "path": "/health", "auth_required": False},
            {"method": "GET", "path": "/projects", "auth_required": True},
            {"method": "POST", "path": "/reports/upload", "auth_required": True},
            {"method": "GET", "path": "/testing/dashboard", "auth_required": True},
        ]
        return {"endpoints": endpoints, "total": len(endpoints)}

    def simulate_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int = 200,
    ) -> dict:
        return {
            "method": method.upper(),
            "path": path,
            "expected_status": status_code,
            "passed": status_code < 400,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "client": API_TEST_CONFIG["client"],
            "endpoint_catalog": self.list_endpoints()["total"] >= 3,
        }
