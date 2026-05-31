from __future__ import annotations

import re

SQL_INJECTION_PATTERNS = [
    r"'\s*OR\s+'1'\s*=\s*'1",
    r"--\s*$",
    r";\s*DROP\s+TABLE",
    r"UNION\s+SELECT",
    r"'\s*;\s*--",
]

SAFE_QUERY_PRACTICES = [
    {"id": "PARAMETERIZED_QUERIES", "description": "Use bound parameters for all user input"},
    {"id": "ORM_ONLY", "description": "Prefer repository/ORM layers over raw SQL"},
    {"id": "INPUT_VALIDATION", "description": "Validate and sanitize identifiers"},
    {"id": "LEAST_PRIVILEGE", "description": "Database roles scoped per service"},
]


class SqlInjectionReviewService:
    def get_review_checklist(self) -> dict:
        return {
            "practices": SAFE_QUERY_PRACTICES,
            "total": len(SAFE_QUERY_PRACTICES),
        }

    def scan_input(self, value: str) -> dict:
        matches: list[str] = []
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                matches.append(pattern)

        return {
            "safe": len(matches) == 0,
            "input_length": len(value),
            "matched_patterns": matches,
            "risk_level": "HIGH" if matches else "LOW",
        }

    def validate_codebase_posture(self) -> dict:
        checks = [
            {"name": "CHECKLIST_DEFINED", "passed": len(SAFE_QUERY_PRACTICES) >= 4},
            {"name": "PATTERNS_CATALOGUED", "passed": len(SQL_INJECTION_PATTERNS) >= 4},
            {"name": "SCANNER_AVAILABLE", "passed": True},
        ]
        return {
            "valid": all(c["passed"] for c in checks),
            "checks": checks,
        }
