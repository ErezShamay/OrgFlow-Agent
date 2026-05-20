from app.services.report_ingestion_service import (
    ReportIngestionService
)


message = {
    "subject":
        "בניין A - דוח פיקוח שבועי",

    "body":
        """
        טרם התקבל אישור כיבוי אש.
        קיימת חריגה בלוחות הזמנים.
        נמצא ליקוי בביצוע עבודות האיטום.
        """
}

service = (
    ReportIngestionService()
)

result = (
    service.process_message(
        message
    )
)

print("\n=== INGESTION RESULT ===\n")

print(result)

print()