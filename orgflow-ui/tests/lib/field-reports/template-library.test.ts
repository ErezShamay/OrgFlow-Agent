import { describe, expect, it } from "vitest";

import {
  countTemplateLibraryItems,
  findTemplateLibraryItem,
  modularBlocksFromTemplateItem,
  TEMPLATE_LIBRARY,
} from "@/lib/field-reports/template-library";

describe("template-library", () => {
  it("includes one template per example PDF", () => {
    expect(countTemplateLibraryItems()).toBe(57);
    expect(TEMPLATE_LIBRARY.length).toBeGreaterThan(0);
  });

  it("builds modular blocks from template item", () => {
    const item = findTemplateLibraryItem("דוח-בדק-בית");
    expect(item).not.toBeNull();
    expect(item?.examplePdf).toBeTruthy();
    const blocks = modularBlocksFromTemplateItem(item!);
    expect(blocks.some((block) => block.kind === "findings_table")).toBe(true);
    expect(blocks.some((block) => block.title_he === "כותרת")).toBe(true);
  });
});
