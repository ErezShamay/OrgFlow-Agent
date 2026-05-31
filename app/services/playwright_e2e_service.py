from __future__ import annotations

PLAYWRIGHT_CONFIG = {
    "browsers": ["chromium", "firefox", "webkit"],
    "base_url": "http://localhost:3000",
    "retries": 2,
    "screenshot_on_failure": True,
}


class PlaywrightE2eService:
    def get_config(self) -> dict:
        return PLAYWRIGHT_CONFIG

    def list_flows(self) -> dict:
        flows = [
            {"id": "login", "steps": 4, "critical": True},
            {"id": "create_project", "steps": 6, "critical": True},
            {"id": "upload_report", "steps": 8, "critical": True},
            {"id": "dashboard_navigation", "steps": 5, "critical": False},
        ]
        return {"flows": flows, "total": len(flows)}

    def evaluate_flow_readiness(self, *, flow_id: str) -> dict:
        flows = {f["id"]: f for f in self.list_flows()["flows"]}
        flow = flows.get(flow_id)
        if not flow:
            return {"found": False, "ready": False}
        return {
            "found": True,
            "flow_id": flow_id,
            "ready": flow["steps"] >= 3,
            "critical": flow["critical"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "browsers": len(PLAYWRIGHT_CONFIG["browsers"]) >= 1,
            "critical_flows": sum(
                1 for f in self.list_flows()["flows"] if f["critical"]
            ),
        }
