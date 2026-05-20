from app.schemas.finding import Finding


class FindingExtractionService:

    FINDING_RULES = [
        {
            "keywords": ["עיכוב", "מתעכב", "טרם"],
            "finding_type": "schedule_delay",
            "severity": "medium",
        },
        {
            "keywords": ["אישור", "היתר"],
            "finding_type": "approval_delay",
            "severity": "medium",
        },
        {
            "keywords": ["חריגה", "ליקוי"],
            "finding_type": "quality_issue",
            "severity": "high",
        },
        {
            "keywords": ["בטיחות", "סיכון"],
            "finding_type": "safety_issue",
            "severity": "critical",
        },
    ]

    def extract_findings(
        self,
        report_text: str,
        report_id: str,
        project_id: str,
    ) -> list[Finding]:

        findings: list[Finding] = []

        lines = [
            line.strip()
            for line in report_text.splitlines()
            if line.strip()
        ]

        for line in lines:

            matched_rule = self._match_rule(line)

            if not matched_rule:
                continue

            finding = Finding(
                report_id=report_id,
                project_id=project_id,
                finding_type=matched_rule["finding_type"],
                severity=matched_rule["severity"],
                title=self._generate_title(line),
                summary=line,
                source_text=line,
            )

            findings.append(finding)

        return findings

    def _match_rule(self, text: str):

        for rule in self.FINDING_RULES:

            for keyword in rule["keywords"]:

                if keyword in text:
                    return rule

        return None

    def _generate_title(self, text: str) -> str:

        if len(text) <= 60:
            return text

        return text[:57] + "..."