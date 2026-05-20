from app.services.ai_review_service import (
    AIReviewService
)


print("\nSTARTING REVIEW QUEUE TEST...\n")

service = (
    AIReviewService()
)

reviews = (
    service.get_pending_reviews()
)

print(f"TOTAL REVIEWS: {len(reviews)}\n")

print("\n=== PENDING REVIEWS ===\n")

for review in reviews:

    print(review)

    print()

print("\nTEST FINISHED\n")