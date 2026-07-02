import type { SupervisionVisitedApartment } from "@/lib/field-reports/schema/types";

/** סיכום טקסטואלי של דירות שנבקרו בביקור אחד. */
export function formatVisitedApartmentsSummaryHe(
  apartments: SupervisionVisitedApartment[]
): string {
  const numbers = apartments
    .map((apartment) => apartment.apartment_number.trim())
    .filter(Boolean);

  if (numbers.length === 0) {
    return "";
  }

  if (numbers.length === 1) {
    return `דירה ${numbers[0]}`;
  }

  return `${numbers.length} דירות: ${numbers.join(", ")}`;
}

export function apartmentSelectionToVisitedApartment(
  selection: {
    apartmentId: string | null;
    apartmentNumber: string;
    ownerName?: string | null;
    adHocApartment: boolean;
  }
): SupervisionVisitedApartment {
  return {
    apartment_id: selection.apartmentId,
    apartment_number: selection.apartmentNumber.trim(),
    owner_name: selection.ownerName ?? null,
    ad_hoc_apartment: selection.adHocApartment,
  };
}
