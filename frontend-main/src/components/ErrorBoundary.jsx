import { Component } from "react";

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error(error, info);
    }
    try {
      const route = window.location?.pathname || "/";
      navigator.sendBeacon?.(
        "/telemetry",
        new Blob([
          JSON.stringify({
            event: "console_render_error",
            properties: {
              route,
              scope: "frontend",
              status: "error",
              command: info?.componentStack ? "react_boundary" : "render"
            }
          })
        ], { type: "application/json" })
      );
    } catch {
      // Rendering fallback is more important than telemetry delivery.
    }
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-error">
          <section>
            <span className="brand-mark">oz</span>
            <h1>Console failed to render</h1>
            <p>{this.state.error.message || "Refresh the page and try again."}</p>
            <button type="button" className="button primary" onClick={() => window.location.reload()}>
              Reload
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
