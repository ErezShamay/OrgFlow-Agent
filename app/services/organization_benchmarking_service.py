class OrganizationBenchmarkingService:
    INDUSTRY_BENCHMARKS = {
        "portfolio_health_index": 78,
        "critical_project_ratio": 0.12,
        "escalation_pressure": 4,
        "operational_load_index": 18,
        "risk_exposure_index": 35,
    }

    def benchmark(
        self,
        portfolio_summary: dict,
        executive_kpis: dict,
    ) -> dict:
        comparisons = []
        deltas = []

        for metric, benchmark_value in self.INDUSTRY_BENCHMARKS.items():
            actual_value = executive_kpis.get(metric)
            if actual_value is None:
                continue

            delta = round(actual_value - benchmark_value, 4)
            if metric in {
                "critical_project_ratio",
                "escalation_pressure",
                "operational_load_index",
                "risk_exposure_index",
            }:
                status = "ABOVE_BENCHMARK" if delta > 0 else "AT_OR_BELOW_BENCHMARK"
            else:
                status = "ABOVE_BENCHMARK" if delta >= 0 else "BELOW_BENCHMARK"

            comparisons.append({
                "metric": metric,
                "actual": actual_value,
                "benchmark": benchmark_value,
                "delta": delta,
                "status": status,
            })
            deltas.append(abs(delta))

        overall_score = 100
        if deltas:
            penalty = min(40, int(sum(deltas) / len(deltas)))
            overall_score = max(0, 100 - penalty)

        return {
            "organization_id": portfolio_summary.get("organization_id"),
            "benchmarks": self.INDUSTRY_BENCHMARKS,
            "comparisons": comparisons,
            "overall_benchmark_score": overall_score,
            "performance_tier": self._performance_tier(overall_score),
        }

    def _performance_tier(self, score: int) -> str:
        if score >= 85:
            return "LEADER"
        if score >= 70:
            return "COMPETITIVE"
        if score >= 50:
            return "DEVELOPING"
        return "LAGGING"
