import { Link } from "react-router-dom";
import { Page } from "../components/ui/index.js";

export function NotFoundPage() {
  return (
    <Page title="Page not found" description="The console route does not exist.">
      <Link className="button secondary" to="/dashboard">Open overview</Link>
    </Page>
  );
}
