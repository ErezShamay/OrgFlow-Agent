import { describe, expect, it } from "vitest";

import {
  apartmentSelectionToVisitedApartment,
  formatVisitedApartmentsSummaryHe,
} from "@/lib/field-reports/visited-apartments-summary";

describe("formatVisitedApartmentsSummaryHe", () => {
  it("formats multiple apartments with count", () => {
    expect(
      formatVisitedApartmentsSummaryHe([
        { apartment_number: "3" },
        { apartment_number: "5" },
        { apartment_number: "12" },
      ])
    ).toBe("3 דירות: 3, 5, 12");
  });

  it("formats a single apartment", () => {
    expect(
      formatVisitedApartmentsSummaryHe([{ apartment_number: "7" }])
    ).toBe("דירה 7");
  });
});

describe("apartmentSelectionToVisitedApartment", () => {
  it("maps picker selection to visited apartment record", () => {
    expect(
      apartmentSelectionToVisitedApartment({
        apartmentId: "apt-1",
        apartmentNumber: " 4 ",
        ownerName: "ישראל",
        adHocApartment: false,
      })
    ).toEqual({
      apartment_id: "apt-1",
      apartment_number: "4",
      owner_name: "ישראל",
      ad_hoc_apartment: false,
    });
  });
});
