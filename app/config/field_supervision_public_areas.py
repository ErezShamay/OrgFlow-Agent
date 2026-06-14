"""Public area definitions for field supervision checklist (spec appendix A)."""

from __future__ import annotations

PUBLIC_AREA_DEFINITIONS: tuple[dict[str, str], ...] = (
    {"id": "LOBBY", "label_he": "לובי / כניסה"},
    {"id": "WET_ROOMS", "label_he": "חדרים רטובים משותפים"},
    {"id": "BALCONY_ROOF", "label_he": "מרפסות / גג משותף"},
    {"id": "PARKING", "label_he": "חניון / מחסנים"},
    {"id": "ELEVATOR_STAIRS", "label_he": "מעליות / חדרי מדרגות"},
    {"id": "OUTDOOR", "label_he": "שטח חוץ / גינון"},
)
