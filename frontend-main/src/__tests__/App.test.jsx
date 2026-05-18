import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.jsx";

const librariesPayload = {
  libraries: [
    {
      vendor: "facebook",
      library: "react",
      version: "19",
      description: "React documentation",
      chunk_count: 2030,
      token_count: 738313,
      indexed_at: "2026-05-18T00:00:00Z"
    }
  ]
};

const statusPayload = {
  status: "operational",
  components: {
    api: { status: "up" },
    postgres: { status: "up" },
    redis: { status: "up" },
    catalog: { libraries: 15 },
    crawler: { queued: 0, running: 0 },
    alerts: { open: 0 }
  }
};

describe("Oz console", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((url) => {
      if (String(url).endsWith("/libraries.json")) {
        return Promise.resolve(jsonResponse(librariesPayload));
      }
      if (String(url).endsWith("/status.json")) {
        return Promise.resolve(jsonResponse(statusPayload));
      }
      return Promise.resolve(jsonResponse({}));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the overview against backend catalog and status data", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("facebook/react")).toBeInTheDocument());
    expect(screen.getByText("Operational")).toBeInTheDocument();
  });

  it("renders sign-in form against backend auth route", () => {
    render(
      <MemoryRouter initialEntries={["/sign-in"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toHaveAttribute("type", "submit");
    expect(document.querySelector("form")).toHaveAttribute("action", "/login");
  });
});

function jsonResponse(payload) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}
