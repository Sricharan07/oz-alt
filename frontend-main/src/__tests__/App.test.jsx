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

const accountPayload = {
  user: {
    id: "user-1",
    email: "dev@tryoz.dev",
    role: "admin",
    is_admin: true
  },
  csrf: "csrf-token",
  web_sessions: [
    {
      id: "web-1",
      current: true,
      created_at: "2026-05-18T00:00:00Z",
      expires_at: "2026-06-18T00:00:00Z",
      revoked_at: ""
    }
  ],
  cli_sessions: [
    {
      id: "cli-1",
      machine_id: "macbook",
      created_at: "2026-05-18T00:00:00Z",
      last_used_at: "2026-05-18T01:00:00Z",
      expires_at: "2026-08-18T00:00:00Z",
      revoked_at: ""
    }
  ],
  usage: {
    totals: { searches: 7, pulls: 3, suggests: 2, libraries: 4 },
    summary: [{ event: "search", library: "facebook/react", count: 7 }],
    daily: [],
    recent_events: [{ event: "search", library: "facebook/react", query_length: 12, result_count: 4, created_at: "2026-05-18T01:00:00Z" }]
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
      if (String(url).endsWith("/api/console/account")) {
        return Promise.resolve(jsonResponse({ error: "unauthorized" }, 401));
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

  it("renders authenticated account state from backend console payload", async () => {
    fetch.mockImplementation((url) => {
      if (String(url).endsWith("/api/console/account")) {
        return Promise.resolve(jsonResponse(accountPayload));
      }
      if (String(url).endsWith("/libraries.json")) {
        return Promise.resolve(jsonResponse(librariesPayload));
      }
      if (String(url).endsWith("/status.json")) {
        return Promise.resolve(jsonResponse(statusPayload));
      }
      return Promise.resolve(jsonResponse({}));
    });

    render(
      <MemoryRouter initialEntries={["/settings"]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("dev@tryoz.dev · admin")).toBeInTheDocument());
    expect(screen.getByText("CLI sessions")).toBeInTheDocument();
    expect(screen.getByText("macbook")).toBeInTheDocument();
    expect(screen.getByText("Usage summary")).toBeInTheDocument();
  });

  it("renders authenticated usage state from backend console payload", async () => {
    fetch.mockImplementation((url) => {
      if (String(url).endsWith("/api/console/account")) {
        return Promise.resolve(jsonResponse(accountPayload));
      }
      return Promise.resolve(jsonResponse({}));
    });

    render(
      <MemoryRouter initialEntries={["/usage"]}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByRole("heading", { name: "Usage" })).toBeInTheDocument());
    expect(screen.getByText("Top activity")).toBeInTheDocument();
    expect(screen.getByText("Recent events")).toBeInTheDocument();
    expect(screen.getAllByText("facebook/react").length).toBeGreaterThan(0);
  });
});

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}
