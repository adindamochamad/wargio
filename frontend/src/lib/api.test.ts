import { describe, expect, it } from "vitest";
import { ekstrakPesanError } from "./api";

describe("ekstrakPesanError", () => {
  it("membaca detail string", () => {
    expect(ekstrakPesanError({ detail: "Not found" }, 404)).toBe("Not found");
  });

  it("membaca detail array validasi FastAPI", () => {
    const body = {
      detail: [
        {
          type: "string_too_short",
          loc: ["body", "pesan"],
          msg: "String should have at least 1 character",
          input: "",
        },
      ],
    };
    expect(ekstrakPesanError(body, 422)).toContain("at least 1 character");
  });

  it("fallback HTTP status", () => {
    expect(ekstrakPesanError(null, 500)).toBe("HTTP 500");
  });
});
