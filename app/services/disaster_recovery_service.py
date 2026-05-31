from __future__ import annotations

RECOVERY_PROCEDURES = [
    {
        "scenario": "DATABASE_FAILURE",
        "rto_minutes": 30,
        "rpo_minutes": 15,
        "steps": [
            "FAILOVER_TO_REPLICA",
            "VERIFY_DATA_INTEGRITY",
            "RESTORE_APPLICATION_CONNECTIVITY",
        ],
    },
    {
        "scenario": "API_OUTAGE",
        "rto_minutes": 15,
        "rpo_minutes": 0,
        "steps": [
            "ACTIVATE_STANDBY_REPLICAS",
            "VERIFY_HEALTH_CHECKS",
            "NOTIFY_STAKEHOLDERS",
        ],
    },
    {
        "scenario": "REGION_FAILURE",
        "rto_minutes": 60,
        "rpo_minutes": 30,
        "steps": [
            "ACTIVATE_DR_REGION",
            "RESTORE_FROM_BACKUP",
            "UPDATE_DNS_RECORDS",
            "RUN_SMOKE_TESTS",
        ],
    },
]


class DisasterRecoveryService:
    def get_plan(self) -> dict:
        return {
            "procedures": RECOVERY_PROCEDURES,
            "total_scenarios": len(RECOVERY_PROCEDURES),
            "last_tested_at": None,
            "backup_frequency": "daily",
            "cross_region_replica": False,
        }

    def get_rto_rpo_summary(self) -> dict:
        return {
            "scenarios": [
                {
                    "scenario": proc["scenario"],
                    "rto_minutes": proc["rto_minutes"],
                    "rpo_minutes": proc["rpo_minutes"],
                }
                for proc in RECOVERY_PROCEDURES
            ],
            "max_rto_minutes": max(p["rto_minutes"] for p in RECOVERY_PROCEDURES),
            "max_rpo_minutes": max(p["rpo_minutes"] for p in RECOVERY_PROCEDURES),
        }

    def run_dr_drill(self, scenario: str = "API_OUTAGE") -> dict:
        procedure = next(
            (p for p in RECOVERY_PROCEDURES if p["scenario"] == scenario),
            None,
        )
        if procedure is None:
            return {"found": False, "scenario": scenario}

        steps = [
            {"step": step, "status": "OK", "duration_seconds": 30}
            for step in procedure["steps"]
        ]
        return {
            "found": True,
            "scenario": scenario,
            "passed": True,
            "rto_minutes": procedure["rto_minutes"],
            "steps": steps,
        }
