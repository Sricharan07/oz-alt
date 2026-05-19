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
import { useMotionProgress } from "../hooks/useMotionProgress.js";
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
      <CatalogHealthCard rows={topRows} totals={totals} operational={operational} loading={librariesLoading} />

      <AccountSnapshot account={account} />

      <section className="summary-grid" aria-label="Catalog summary">
        <Metric label="Libraries" value={librariesLoading ? "Loading" : integer(totals.libraries)} icon={Library} />
        <Metric label="Chunks" value={compactNumber(totals.chunks)} icon={FileText} />
        <Metric label="Tokens" value={compactNumber(totals.tokens)} icon={Database} />
        <Metric label="System" value={operational ? "Operational" : "Check status"} icon={operational ? CheckCircle2 : CircleAlert} tone={operational ? "ok" : "warn"} />
      </section>

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
        <SectionHeader title="Recent catalog" action={<Link to="/libraries">Browse all <ChevronRight size={15} /></Link>} />
        <LibraryTable rows={rows.slice(0, 8)} loading={librariesLoading} compact />
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

function CatalogHealthCard({ rows, totals, operational, loading }) {
  const progress = useMotionProgress(`${rows.length}:${totals.chunks}:${loading}`);
  const maxChunks = Math.max(...rows.map((row) => Number(row.chunk_count || 0)), 1);

  return (
    <section className="overview-usage-card" aria-label="Catalog health">
      <div className="overview-usage-header">
        <div>
          <h2>Catalog health</h2>
          <span>{operational ? "Production registry is serving current packs" : "Status endpoint needs attention"}</span>
        </div>
        <Link className="overview-usage-link" to="/status">
          Status
          <ChevronRight size={14} aria-hidden="true" />
        </Link>
      </div>
      <div className="overview-usage-body">
        <div className="overview-usage-left">
          <div className="overview-metrics-row">
            <div className="overview-metric-block">
              <div className="overview-metric-circle circle-solid">{integer(Math.round(totals.libraries * progress))}</div>
              <div className="overview-metric-info">
                <h3>Libraries</h3>
                <p>Promoted packs</p>
              </div>
            </div>
            <div className="overview-metric-block">
              <div className="overview-metric-circle circle-dashed">{compactNumber(Math.round(totals.chunks * progress))}</div>
              <div className="overview-metric-info">
                <h3>Chunks</h3>
                <p>Searchable docs</p>
              </div>
            </div>
          </div>
          <div className="overview-usage-totals">
            <StatPair label="Token corpus" value={compactNumber(Math.round(totals.tokens * progress))} />
            <StatPair label="API base" value="api.tryoz.dev" />
            <StatPair label="Agent mode" value="Path-first" />
          </div>
        </div>
        <div className="overview-usage-right">
          <div className="overview-chart-container" aria-label="Top libraries by chunks">
            {rows.map((row) => {
              const height = Math.max(10, Math.round((Number(row.chunk_count || 0) / maxChunks) * 100 * progress));
              return (
                <Link
                  key={`${row.vendor}/${row.library}`}
                  to={`/libraries/${encodeURIComponent(row.vendor)}/${String(row.library).split("/").map(encodeURIComponent).join("/")}`}
                  className="overview-chart-bar"
                  style={{ height: `${height}%`, "--bar-alpha": String(Math.max(0.18, height / 140)) }}
                  data-tooltip={`${row.vendor}/${row.library}: ${integer(row.chunk_count)} chunks`}
                  aria-label={`${row.vendor}/${row.library}`}
                />
              );
            })}
          </div>
          <div className="overview-chart-labels">
            <span>smaller</span>
            <span>top indexed packs</span>
            <span>larger</span>
          </div>
        </div>
      </div>
    </section>
  );
}
