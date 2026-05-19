import { afterEach, describe, expect, it, vi } from "vitest";
import { apiUrl, approveDeviceCode, changePassword, postJson, safeJson } from "../api.js";

describe("api helpers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses same-origin URLs when no runtime API base is configured", () => {
    vi.stubGlobal("__OZ_CONFIG__", { apiBaseUrl: "" });
    expect(apiUrl("/libraries.json")).toBe("/libraries.json");
  });

  it("parses JSON bodies safely", async () => {
    const response = new Response(JSON.stringify({ ok: true }));
    await expect(safeJson(response)).resolves.toEqual({ ok: true });
  });

  it("posts JSON payloads with credentials", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true }))));
    vi.stubGlobal("fetch", fetchMock);

    await expect(postJson("/api/console/cli-sessions/revoke", { token_id: "abc" })).resolves.toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/console/cli-sessions/revoke",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ token_id: "abc" })
      })
    );
  });

  it("sends password changes through the console API", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true }))));
    vi.stubGlobal("fetch", fetchMock);

    await changePassword({
      currentPassword: "old-password-123",
      newPassword: "new-password-123",
      confirmPassword: "new-password-123",
      csrf: "csrf"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/console/password",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          current_password: "old-password-123",
          new_password: "new-password-123",
          confirm_password: "new-password-123",
          csrf: "csrf"
        })
      })
    );
  });

  it("sends device approvals through the console API", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true }))));
    vi.stubGlobal("fetch", fetchMock);

    await approveDeviceCode("ABCD-EFGH", "csrf");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/console/device/approve",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          user_code: "ABCD-EFGH",
          csrf: "csrf"
        })
      })
    );
  });
});
