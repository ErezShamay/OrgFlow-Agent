import type { Content } from "pdfmake/interfaces";

import { PDF_HEBREW_FONT, pdfText } from "./pdf-styles";
import { PDF_SUPERVISION_BANNER_HE } from "./render-header";
import type { OrganizationProfileSnapshot } from "./types";

/** שוליים עליונים - משאירים מקום לכותרת חוזרת כמו בדוחות הלקוח. */
export const PDF_PAGE_MARGINS: [number, number, number, number] = [
  40,
  92,
  40,
  52,
];

export function formatPdfVisitDateHe(value: string | undefined): string {
  if (!value?.trim()) {
    return "";
  }

  const trimmed = value.trim();
  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(trimmed);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    return `${day}.${month}.${year}`;
  }

  const dotted = /^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$/.exec(trimmed);
  if (dotted) {
    return trimmed;
  }

  const parsed = new Date(trimmed.length === 10 ? `${trimmed}T12:00:00` : trimmed);
  if (!Number.isNaN(parsed.getTime())) {
    const day = String(parsed.getDate()).padStart(2, "0");
    const month = String(parsed.getMonth() + 1).padStart(2, "0");
    const year = parsed.getFullYear();
    return `${day}.${month}.${year}`;
  }

  return trimmed;
}

export function organizationBannerLabel(
  profile: OrganizationProfileSnapshot | null | undefined
): string {
  const parts = [
    profile?.organization_name,
    profile?.report_tagline,
  ].filter(Boolean);
  return parts.join(" - ") || "פיקוח הנדסי";
}

/**
 * כותרת עליונה בכל עמוד - באנר, תאריך, שם המפקח/ארגון, מספר עמוד (כמו 7/7 דוחות דוגמה).
 */
export function renderRepeatingPageHeader(input: {
  visitDate: string;
  profile?: OrganizationProfileSnapshot | null;
}): (currentPage: number, pageCount: number) => Content {
  const visitDateLabel = formatPdfVisitDateHe(input.visitDate);
  const orgLabel = organizationBannerLabel(input.profile);

  return (currentPage: number) => ({
    margin: [40, 16, 40, 0],
    stack: [
      pdfText(PDF_SUPERVISION_BANNER_HE, {
        style: "supervisionBanner",
        alignment: "center",
        margin: [0, 0, 0, 4],
      }),
      {
        columns: [
          {
            width: "auto",
            text: visitDateLabel,
            font: PDF_HEBREW_FONT,
            fontSize: 9,
            alignment: "right",
            direction: "rtl",
          },
          {
            width: "*",
            text: orgLabel,
            font: PDF_HEBREW_FONT,
            fontSize: 9,
            alignment: "center",
            direction: "rtl",
          },
          {
            width: "auto",
            text: `עמוד ${currentPage}`,
            font: PDF_HEBREW_FONT,
            fontSize: 9,
            alignment: "left",
            direction: "rtl",
          },
        ],
        columnGap: 10,
      },
    ],
  });
}
