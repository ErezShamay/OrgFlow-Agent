import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  getSystemNavLinks,
} from "@/lib/navigation";
import { getQCPrimaryNavLinks } from "@/lib/qc-navigation";
import {
  QCFrozenFeatureError,
  assertNotFrozenForFeature,
  getFrozenSurfaceForApiPath,
  isFrozenApiPath,
  isFrozenSurface,
} from "@/lib/qc-freeze";

const REPO_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("stage 5.6 gate (freeze Agent Orchestrator)", () => {
  it("marks agent orchestrator as frozen with /agent/run API path", () => {
    expect(isFrozenSurface("agent_orchestrator")).toBe(true);
    expect(isFrozenApiPath("/agent/run")).toBe(true);

    const surface = getFrozenSurfaceForApiPath("/agent/run");
    expect(surface?.id).toBe("agent_orchestrator");
    expect(surface?.qcReplacement).toContain("materialization");
  });

  it("blocks feature work on frozen agent orchestrator surface", () => {
    expect(() => assertNotFrozenForFeature("agent_orchestrator")).toThrow(
      QCFrozenFeatureError
    );
    expect(() => assertNotFrozenForFeature("upload_legacy")).not.toThrow();
  });

  it("does not expose agent orchestrator in any primary navigation", () => {
    const allNavHrefs = [
      ...GLOBAL_NAV_LINKS.map((link) => link.href),
      ...HOME_NAVBAR_LINKS.map((link) => link.href),
      ...getQCPrimaryNavLinks({ role: "SUPERVISOR" }).map((link) => link.href),
      ...getSystemNavLinks(true).map((link) => link.href),
      ...getSystemNavLinks(false).map((link) => link.href),
    ];

    expect(allNavHrefs.some((href) => href.includes("/agent"))).toBe(false);
  });

  it("documents freeze in orchestrator module and guards API in main", () => {
    const orchestrator = readSource("app/agent/orchestrator.py");
    const main = readSource("app/main.py");

    expect(orchestrator).toContain("QC freeze (stage 5.6)");
    expect(orchestrator).toContain("Agent Orchestrator");
    expect(main).toContain("raise_if_frozen_api_path");
    expect(main).toContain('raise_if_frozen_api_path("/agent/run")');
  });
});
