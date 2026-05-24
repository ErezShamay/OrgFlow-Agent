from app.services.ai_review_service import (
    AIReviewService
)


service = (
    AIReviewService()
)

pending_reviews = (
    service.get_pending_reviews()
)

if not pending_reviews:

    print(
        "\nNO PENDING REVIEWS\n"
    )

    exit()

review = pending_reviews[0]

print("\n=== APPROVING REVIEW ===\n")

print(review)

print()

result = (
    service.approve_review(
        interpretation_id=
            review["id"],

        reviewed_by=
            "ארז שמאי",

        review_notes=
            "Approved for operational follow-up"
    )
)

print("\n=== APPROVAL RESULT ===\n")

print(result)

print()