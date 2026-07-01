import { describe, expect, it } from "vitest";

import {
  getLegalDocument,
  LEGAL_DOCUMENTS,
  listLegalDocuments,
  LOGIN_LEGAL_DOCUMENTS,
} from "@/lib/legal/documents";

describe("legal documents", () => {
  it("lists all three legal documents", () => {
    expect(listLegalDocuments()).toHaveLength(3);
    expect(LOGIN_LEGAL_DOCUMENTS).toHaveLength(3);
  });

  it("resolves known slugs to downloadable documents", () => {
    expect(getLegalDocument("terms")).toEqual(LEGAL_DOCUMENTS.terms);
    expect(getLegalDocument("privacy")?.downloadHref).toBe(
      "/legal/privacy-policy.docx"
    );
    expect(getLegalDocument("ai-transparency")?.href).toBe(
      "/legal/ai-transparency"
    );
  });

  it("returns undefined for unknown slugs", () => {
    expect(getLegalDocument("unknown")).toBeUndefined();
  });
});
