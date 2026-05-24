from app.services.operational_action_service import (
    OperationalActionService
)


service = (
    OperationalActionService()
)

actions = (
    service.get_open_actions()
)

print("\n=== OPEN ACTIONS ===\n")

for action in actions:

    print(action)

    print()

print("\n=== ESCALATIONS ===\n")

escalations = (
    service.get_escalations()
)

for escalation in escalations:

    print(escalation)

    print()