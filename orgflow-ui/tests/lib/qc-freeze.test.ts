import { describe, expect, it } from "vitest";

import { QC_DEPRECATED_PRIMARY_ROUTES } from "@/lib/qc-navigation";
import {
  QC_FROZEN_SURFACES,
  isAllowedQcException,
  isDeprecatedRoute,
  isFrozenApiPath,
  isFrozenSurface,
  listSurfacesByCategory,
  shouldHideFromPrimaryNav,
  assertNotFrozenForFeature,
  getFrozenSurfaceForApiPath,
  QCFrozenFeatureError,
} from "@/lib/qc-freeze";

describe("qc freeze list (spec 0.5)", () => {
  it("defines frozen, deprecated, admin, and secondary surfaces", () => {
    expect(QC_FROZEN_SURFACES.length).toBeGreaterThanOrEqual(14);
    expect(listSurfacesByCategory("FROZEN").length).toBeGreaterThanOrEqual(6);
    expect(listSurfacesByCategory("DEPRECATED").length).toBeGreaterThanOrEqual(
      5
    );
    expect(listSurfacesByCategory("ADMIN_ONLY")).toHaveLength(2);
    expect(listSurfacesByCategory("SECONDARY")).toHaveLength(1);
  });

  it("marks agent orchestrator as frozen", () => {
    expect(isFrozenSurface("agent_orchestrator")).toBe(true);
    expect(isFrozenSurface("upload_legacy")).toBe(false);
  });

  it("detects deprecated UI routes", () => {
    expect(isDeprecatedRoute("/upload")).toBe(true);
    expect(isDeprecatedRoute("/reviews")).toBe(true);
    expect(isDeprecatedRoute("/portfolio")).toBe(false);
    expect(shouldHideFromPrimaryNav("/actions")).toBe(true);
  });

  it("detects frozen API paths for QC flows", () => {
    expect(isFrozenApiPath("/agent/run")).toBe(true);
    expect(isFrozenApiPath("/reports/upload")).toBe(true);
    expect(isFrozenApiPath("/projects/abc/issues")).toBe(false);
  });

  it("aligns qc-navigation deprecated routes with freeze list", () => {
    for (const route of QC_DEPRECATED_PRIMARY_ROUTES) {
      expect(isDeprecatedRoute(route.href)).toBe(true);
    }
  });

  it("allows documented QC exceptions", () => {
    expect(isAllowedQcException("NotificationTool")).toBe(true);
    expect(isAllowedQcException("Orchestrator")).toBe(false);
  });

  it("assertNotFrozenForFeature blocks agent orchestrator (stage 5.6)", () => {
    expect(() => assertNotFrozenForFeature("agent_orchestrator")).toThrow(
      QCFrozenFeatureError
    );
    expect(() => assertNotFrozenForFeature("upload_legacy")).not.toThrow();
  });

  it("resolves frozen surface for /agent/run API path", () => {
    const surface = getFrozenSurfaceForApiPath("/agent/run");
    expect(surface?.id).toBe("agent_orchestrator");
  });
});
