import { describe, expect, it } from "vitest";

import {
  EMAIL_INVALID_MESSAGE,
  isValidEmail,
  validateEmail,
  validateOptionalEmail,
  validateProjectEmails,
} from "@/lib/validation/email";

describe("email validation", () => {
  it("accepts standard and co.il addresses", () => {
    expect(isValidEmail("erez@erez.com")).toBe(true);
    expect(isValidEmail("user.name+tag@example.co.il")).toBe(true);
    expect(isValidEmail("noa@company.org.il")).toBe(true);
  });

  it("rejects malformed addresses", () => {
    expect(isValidEmail("not-an-email")).toBe(false);
    expect(isValidEmail("user@domain")).toBe(false);
    expect(isValidEmail("@example.com")).toBe(false);
  });

  it("returns a Hebrew error message for invalid required email", () => {
    expect(validateEmail("bad-email")).toBe(EMAIL_INVALID_MESSAGE);
  });

  it("allows empty optional email", () => {
    expect(validateOptionalEmail("")).toBeNull();
    expect(validateOptionalEmail("   ")).toBeNull();
  });

  it("validates all project email fields", () => {
    const form = {
      developer_email: "dev@example.com",
      contractor_email: "build@example.com",
      developer_pm_email: "pm@example.com",
      lawyer_email: "legal@example.com",
      accompanying_lawyer_email: "cohen@example.com",
      supervisor_email: "invalid",
      architect_email: "arch@example.com",
      site_manager_email: "site@example.com",
    };

    expect(validateProjectEmails(form)).toBe(EMAIL_INVALID_MESSAGE);
  });
});
