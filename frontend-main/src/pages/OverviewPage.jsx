import {
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Database,
  FileText,
  Library
} from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { getStatus, listLibraries } from "../api.js";
import { Checklist, CommandBlock, LibraryTable, Metric, Page, Panel, SectionHeader, StatPair } from "../components/ui/index.js";
import { compactNumber, integer } from "../format.js";
import { useAsync } from "../hooks/useAsync.js";
import { useConsoleAccount } from "../hooks/useConsoleAccount.js";
import { summarizeLibraries, topLibraries } from "./pageData.js";

export function OverviewPage() {
  const { data: libraries, loading: librariesLoading } = useAsync(listLibraries, []);
  const { data: status } = useAsync(getStatus, null);
  const account = useConsoleAccount();
  const rows = useMemo(() => libraries || [], [libraries]);
  const totals = useMemo(() => summarizeLibraries(rows), [rows]);
  const topRows = useMemo(() => topLibraries(rows), [rows]);
  const operational = status?.status === "operational";

  return (
    <Page title="Overview" description="A console for authenticated CLI access, curated library packs, and local docs for agents.">
      <section className="summary-grid" aria-label="Catalog summary">
        <Metric label="Libraries" value={librariesLoading ? "Loading" : integer(totals.libraries)} icon={Library} />
        <Metric label="Chunks" value={compactNumber(totals.chunks)} icon={FileText} />
        <Metric label="Tokens" value={compactNumber(totals.tokens)} icon={Database} />
        <Metric label="System" value={operational ? "Operational" : "Check status"} icon={operational ? CheckCircle2 : CircleAlert} tone={operational ? "ok" : "warn"} />
      </section>

      <AccountSnapshot account={account} />

      <div className="two-column">
        <Panel>
          <SectionHeader title="Start from a project" />
          <CommandBlock
            lines={[
              "npm install -g @hiringbae/oz",
              "oz login --api-url https://api.tryoz.dev",
              "oz init",
              'oz suggest "Next.js middleware auth"',
              "oz pull vercel/next.js",
              'oz search "cookies middleware jwt" vercel/next.js'
            ]}
          />
        </Panel>
        <Panel>
          <SectionHeader title="Agent workflow" />
          <Checklist
            items={[
              "Use oz suggest when the library is unknown.",
              "Use oz pull to materialize docs under .codo/vendors.",
              "Use oz search for semantic path discovery.",
              "Use rg/read/glob on pulled Markdown files for final context.",
              "Use oz prune when local docs need cleanup."
            ]}
          />
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="Catalog" action={<Link to="/libraries">Browse all <ChevronRight size={15} /></Link>} />
        <div className="catalog-overview">
          <div className="catalog-overview-summary">
            <StatPair label="Indexed files" value={integer(rows.reduce((sum, row) => sum + Number(row.file_count || 0), 0))} />
            <StatPair label="Largest pack" value={topRows[0] ? `${topRows[0].vendor}/${topRows[0].library}` : "Not recorded"} />
            <StatPair label="API base" value="api.tryoz.dev" />
          </div>
          <LibraryTable rows={topRows.length ? topRows : rows.slice(0, 8)} loading={librariesLoading} compact />
        </div>
      </Panel>
    </Page>
  );
}

function AccountSnapshot({ account }) {
  if (account.loading) {
    return null;
  }

  if (!account.authenticated) {
    return (
      <Panel className="account-snapshot">
        <SectionHeader title="Connect your CLI account" action={<Link to="/sign-in">Sign in</Link>} />
        <Checklist
          items={[
            "Create or sign into the same account used by oz login.",
            "Approve the CLI device from the browser.",
            "Usage and active CLI sessions appear here after the first search or pull."
          ]}
        />
      </Panel>
    );
  }

  const totals = account.usage?.totals || {};
  return (
    <Panel className="account-snapshot">
      <SectionHeader title="Your workspace" action={<Link to="/settings">Manage account</Link>} />
      <div className="account-snapshot-grid">
        <StatPair label="Signed in as" value={account.user.email} />
        <StatPair label="CLI sessions" value={integer(account.cliSessions.filter((row) => !row.revoked_at).length)} />
        <StatPair label="Searches" value={integer(totals.searches)} />
        <StatPair label="Pulls" value={integer(totals.pulls)} />
      </div>
    </Panel>
  );
}
