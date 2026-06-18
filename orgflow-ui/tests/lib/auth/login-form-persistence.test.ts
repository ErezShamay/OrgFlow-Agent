import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearSavedLoginEmail,
  readSavedLoginEmail,
  saveLoginEmail,
} from "@/lib/auth/login-form-persistence";

describe("login-form-persistence", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", {
      store: {} as Record<string, string>,
      getItem(key: string) {
        return this.store[key] ?? null;
      },
      setItem(key: string, value: string) {
        this.store[key] = value;
      },
      removeItem(key: string) {
        delete this.store[key];
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("readSavedLoginEmail returns empty when unset", () => {
    expect(readSavedLoginEmail()).toBe("");
  });

  it("saveLoginEmail persists trimmed email", () => {
    saveLoginEmail("  user@example.com  ");
    expect(readSavedLoginEmail()).toBe("user@example.com");
  });

  it("clearSavedLoginEmail removes saved email", () => {
    saveLoginEmail("user@example.com");
    clearSavedLoginEmail();
    expect(readSavedLoginEmail()).toBe("");
  });
});
