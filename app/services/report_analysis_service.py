class ReportAnalysisService:
    def analyze_report(
        self,
        report_text
    ):
        lowered_text = (
            report_text.lower()
        )

        findings = []

        issue_patterns = [
            {
                "keywords":
                    [
                        "delay",
                        "עיכוב"
                    ],

                "issue_type":
                    "DELAY",

                "severity":
                    "HIGH",

                "recommended_action":
                    (
                        "Review project "
                        "timeline and "
                        "mitigation plan."
                    )
            },
            {
                "keywords":
                    [
                        "blocked",
                        "חסם"
                    ],

                "issue_type":
                    "BLOCKER",

                "severity":
                    "HIGH",

                "recommended_action":
                    (
                        "Escalate blocker "
                        "to operations "
                        "manager."
                    )
            },
            {
                "keywords":
                    [
                        "risk",
                        "סיכון"
                    ],

                "issue_type":
                    "RISK",

                "severity":
                    "MEDIUM",

                "recommended_action":
                    (
                        "Review risk "
                        "assessment."
                    )
            },
            {
                "keywords":
                    [
                        "safety",
                        "בטיחות"
                    ],

                "issue_type":
                    "SAFETY",

                "severity":
                    "CRITICAL",

                "recommended_action":
                    (
                        "Immediate safety "
                        "review required."
                    )
            }
        ]

        for pattern in issue_patterns:
            for keyword in (
                pattern["keywords"]
            ):
                if keyword in lowered_text:
                    findings.append({
                        "issue_type":
                            pattern[
                                "issue_type"
                            ],

                        "severity":
                            pattern[
                                "severity"
                            ],

                        "matched_keyword":
                            keyword,

                        "recommended_action":
                            pattern[
                                "recommended_action"
                            ]
                    })

                    break

        if len(findings) == 0:
            overall_status = (
                "HEALTHY"
            )
        else:
            overall_status = (
                "ATTENTION_REQUIRED"
            )

        return {
            "overall_status":
                overall_status,

            "findings":
                findings,

            "finding_count":
                len(findings)
        }