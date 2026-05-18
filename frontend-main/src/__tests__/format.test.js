import { describe, expect, it } from "vitest";
import { bytes, compactNumber, libraryPath, statusClass } from "../format.js";

describe("format helpers", () => {
  it("formats catalog counts for compact display", () => {
    expect(compactNumber(15320)).toBe("15.3K");
  });

  it("formats byte counts", () => {
    expect(bytes(1536)).toBe("1.5 KB");
  });

  it("builds stable library routes", () => {
    expect(libraryPath({ vendor: "vercel", library: "next.js" })).toBe("/libraries/vercel/next.js");
  });

  it("normalizes component status classes", () => {
    expect(statusClass("up")).toBe("ok");
    expect(statusClass("down")).toBe("warn");
  });
});
