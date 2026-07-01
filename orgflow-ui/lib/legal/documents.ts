export type LegalDocumentSlug =
  | "terms"
  | "privacy"
  | "ai-transparency";

export type LegalDocument = {
  slug: LegalDocumentSlug;
  title: string;
  description: string;
  fileName: string;
  href: string;
  downloadHref: string;
};

const LEGAL_BASE_PATH = "/legal";

export const LEGAL_DOCUMENTS: Record<LegalDocumentSlug, LegalDocument> = {
  terms: {
    slug: "terms",
    title: "תנאי שימוש",
    description: "תנאי השימוש במערכת ElayoAI",
    fileName: "terms-of-service.docx",
    href: `${LEGAL_BASE_PATH}/terms`,
    downloadHref: `${LEGAL_BASE_PATH}/terms-of-service.docx`,
  },
  privacy: {
    slug: "privacy",
    title: "מדיניות פרטיות",
    description: "מדיניות הפרטיות והגנת המידע במערכת ElayoAI",
    fileName: "privacy-policy.docx",
    href: `${LEGAL_BASE_PATH}/privacy`,
    downloadHref: `${LEGAL_BASE_PATH}/privacy-policy.docx`,
  },
  "ai-transparency": {
    slug: "ai-transparency",
    title: "מדיניות שקיפות AI",
    description: "מדיניות השקיפות והשימוש בבינה מלאכותית במערכת ElayoAI",
    fileName: "ai-transparency-policy.docx",
    href: `${LEGAL_BASE_PATH}/ai-transparency`,
    downloadHref: `${LEGAL_BASE_PATH}/ai-transparency-policy.docx`,
  },
};

export const LOGIN_LEGAL_DOCUMENTS = [
  LEGAL_DOCUMENTS.terms,
  LEGAL_DOCUMENTS.privacy,
  LEGAL_DOCUMENTS["ai-transparency"],
] as const;

export function getLegalDocument(
  slug: string
): LegalDocument | undefined {
  if (slug in LEGAL_DOCUMENTS) {
    return LEGAL_DOCUMENTS[slug as LegalDocumentSlug];
  }

  return undefined;
}

export function listLegalDocuments(): LegalDocument[] {
  return Object.values(LEGAL_DOCUMENTS);
}
