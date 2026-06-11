/**
 * מנקה תווים שעלולים להופיע כריבועים ב-NotoSansHebrew / pdfmake.
 */
export function sanitizePdfHebrewText(text: string): string {
  return text
    .replace(/\u2014/g, "-")
    .replace(/\u2013/g, "-")
    .replace(/\u05F4/g, '"')
    .replace(/\u05F3/g, "'")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/\u00AB/g, '"')
    .replace(/\u00BB/g, '"')
    .replace(/\u2026/g, "...")
    .replace(/\u00A0/g, " ");
}
