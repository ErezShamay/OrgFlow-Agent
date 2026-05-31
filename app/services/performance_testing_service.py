from __future__ import annotations

PERFORMANCE_TEST_CONFIG = {
    "tool": "pytest-benchmark",
    "warmup_iterations": 3,
    "thresholds_ms": {"p50": 100, "p95": 500, "p99": 1000},
}


class PerformanceTestingService:
    def get_config(self) -> dict:
        return PERFORMANCE_TEST_CONFIG

    def list_benchmarks(self) -> dict:
        benchmarks = [
            {"id": "project_list", "endpoint": "GET /projects", "budget_p95_ms": 200},
            {"id": "report_search", "endpoint": "GET /reports/search", "budget_p95_ms": 350},
            {"id": "portfolio_dashboard", "endpoint": "GET /portfolio/dashboard", "budget_p95_ms": 500},
        ]
        return {"benchmarks": benchmarks, "total": len(benchmarks)}

    def evaluate_benchmark(
        self,
        *,
        benchmark_id: str,
        p95_ms: float,
    ) -> dict:
        benchmarks = {b["id"]: b for b in self.list_benchmarks()["benchmarks"]}
        benchmark = benchmarks.get(benchmark_id)
        if not benchmark:
            return {"found": False, "passed": False}
        return {
            "found": True,
            "benchmark_id": benchmark_id,
            "p95_ms": p95_ms,
            "budget_p95_ms": benchmark["budget_p95_ms"],
            "passed": p95_ms <= benchmark["budget_p95_ms"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "tool": PERFORMANCE_TEST_CONFIG["tool"],
            "benchmark_count": self.list_benchmarks()["total"] >= 2,
        }
