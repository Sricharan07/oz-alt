import { describe, expect, it, vi } from "vitest";
import { apiUrl, safeJson } from "../api.js";

describe("api helpers", () => {
  it("uses same-origin URLs when no runtime API base is configured", () => {
    vi.stubGlobal("__OZ_CONFIG__", { apiBaseUrl: "" });
    expect(apiUrl("/libraries.json")).toBe("/libraries.json");
    vi.unstubAllGlobals();
  });

  it("parses JSON bodies safely", async () => {
    const response = new Response(JSON.stringify({ ok: true }));
    await expect(safeJson(response)).resolves.toEqual({ ok: true });
  });
});
