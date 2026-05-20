from app.services.finding_query_service import (
    FindingQueryService
)


service = (
    FindingQueryService()
)

print("\n=== OPEN FINDINGS ===\n")

findings = (
    service.get_open_findings()
)

for finding in findings:

    print(finding)

    print()