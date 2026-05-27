from app.schemas.finding import Finding


class FindingExtractionService:

    FINDING_PATTERNS = {
        "approval_delay": {
            "signals": {
                "אישור": 4,
                "היתר": 4,
                "טרם התקבל": 5,
                "ממתין": 3,
            },
            "severity": "medium",
        },

        "schedule_delay": {
            "signals": {
                "עיכוב": 4,
                "מתעכב": 4,
                "לוחות זמנים": 5,
                "מעכב": 3,
            },
            "severity": "medium",
        },

        "quality_issue": {
            "signals": {
                "ליקוי": 5,
                "ביצוע": 2,
                "אי התאמה": 4,
                "חריגה": 1,
            },
            "severity": "high",
        },

        "safety_issue": {
            "signals": {
                "בטיחות": 5,
                "סכנה": 5,
                "מפגע": 4,
                "סיכון": 3,
            },
            "severity": "critical",
        },

        "documentation_gap": {
            "signals": {
                "חסר מסמך": 5,
                "לא הוצג": 4,
                "חסר אישור": 4,
                "לא נמסר": 4,
            },
            "severity": "medium",
        },
    }

    FINDING_PRIORITY = [
        "safety_issue",
        "quality_issue",
        "schedule_delay",
        "approval_delay",
        "documentation_gap",
    ]

    PREFIXES = [
        "ב",
        "ל",
        "כ",
        "ו",
        "ה",
    ]

    def extract_findings(
        self,
        report_text: str,
        report_id: str,
        project_id: str,
    ) -> list[Finding]:

        findings = []

        lines = self._split_text(
            report_text
        )

        for line in lines:

            classification = (
                self._classify_line(line)
            )

            if not classification:
                continue

            finding = Finding(
                report_id=report_id,

                project_id=project_id,

                finding_type=classification[
                    "finding_type"
                ],

                severity=classification[
                    "severity"
                ],

                title=self._generate_title(
                    line
                ),

                summary=line,

                source_text=line,
            )

            findings.append(
                finding
            )

        return findings

    def _split_text(
        self,
        text: str
    ) -> list[str]:

        lines = []

        for raw_line in (
            text.splitlines()
        ):

            line = raw_line.strip()

            if not line:
                continue

            lines.append(line)

        return lines

    def _normalize_word(
        self,
        word: str
    ) -> str:

        normalized_word = word

        for prefix in self.PREFIXES:

            if (
                word.startswith(prefix)
                and len(word) > 3
            ):

                normalized_word = (
                    word[1:]
                )

                break

        return normalized_word

    def _normalize_text(
        self,
        text: str
    ) -> str:

        words = text.split()

        normalized_words = []

        for word in words:

            normalized_words.append(
                self._normalize_word(
                    word
                )
            )

        return " ".join(
            normalized_words
        )

    def _classify_line(
        self,
        text: str
    ):

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        normalized_words = (
            normalized_text.split()
        )

        scores = {}

        for (
            finding_type,
            config
        ) in (
            self.FINDING_PATTERNS
            .items()
        ):

            score = 0

            for (
                signal,
                weight
            ) in (
                config["signals"]
                .items()
            ):

                if " " in signal:

                    if signal in normalized_text:
                        score += weight

                else:

                    for word in normalized_words:

                        if signal == word:
                            score += weight

            if score > 0:

                scores[
                    finding_type
                ] = {
                    "score": score,

                    "severity":
                    config["severity"]
                }

        if not scores:
            return None

        best_match = max(
            scores.items(),
            key=lambda item: (
                item[1]["score"],
                -self.FINDING_PRIORITY.index(
                    item[0]
                ),
            )
        )

        finding_type = (
            best_match[0]
        )

        severity = (
            best_match[1]["severity"]
        )

        return {
            "finding_type":
                finding_type,

            "severity":
                severity
        }

    def _generate_title(
        self,
        text: str
    ) -> str:

        if len(text) <= 80:
            return text

        return text[:77] + "..."
