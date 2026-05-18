import {
  Activity,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Database,
  ExternalLink,
  FileText,
  Gauge,
  KeyRound,
  Library,
  LogIn,
  Menu,
  Monitor,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  Shield,
  Terminal,
  UserRound
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import { getLibrary, getStatus, listLibraries } from "./api.js";
import { runtimeConfig } from "./config.js";
import { bytes, compactNumber, dateText, integer, libraryId, libraryPath, percent, statusClass } from "./format.js";

const navItems = [
  { to: "/dashboard", label: "Overview", icon: Activity },
  { to: "/libraries", label: "Libraries", icon: Library },
  { to: "/setup", label: "Setup", icon: Terminal },
  { to: "/status", label: "Status", icon: Gauge },
  { to: "/settings", label: "Account", icon: UserRound }
];

export default function App() {
  return (
    <Routes>
      <Route path="/sign-in" element={<AuthPage mode="login" />} />
      <Route path="/sign-up" element={<AuthPage mode="signup" />} />
      <Route path="/*" element={<ConsoleLayout />} />
    </Routes>
  );
}

function ConsoleLayout() {
  const config = runtimeConfig();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <div className={`dashboard-layout ${mobileOpen ? "sidebar-open" : ""} ${collapsed ? "sidebar-collapsed" : ""}`}>
      <header className="topbar">
        <button
          type="button"
          className="mobile-nav-toggle"
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          <Menu size={15} aria-hidden="true" />
          {mobileOpen ? "Close" : "Menu"}
        </button>
        <Link className={`topbar-brand ${collapsed ? "collapsed" : ""}`} to="/dashboard" aria-label="Oz dashboard">
          <span className="brand-mark">oz</span>
          {!collapsed ? <span className="topbar-brand-text">Console</span> : null}
        </Link>
        <div className="right-container">
          <div className="top-buttons">
            <Link className="top-button search-bar" to="/libraries">
              <Search size={15} aria-hidden="true" />
              <span>Search catalog</span>
            </Link>
            <a className="top-button" href="/device" aria-label="Approve CLI device">
              <KeyRound size={15} aria-hidden="true" />
              <span>Device</span>
            </a>
            <Link className="top-button" to="/sign-in" aria-label="Sign in">
              <LogIn size={15} aria-hidden="true" />
              <span>Sign in</span>
            </Link>
          </div>
        </div>
      </header>
      <div className="main-container">
        <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
          <nav className="nav-links" aria-label="Primary navigation">
            <div className="nav-group">
              <div className="nav-group-label">Console</div>
              <div className="sub-links">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) => `sub-link-content ${isActive ? "active" : ""}`}
                  >
                    <span className="sidebar-icon">
                      <item.icon size={18} aria-hidden="true" />
                    </span>
                    {!collapsed ? <p>{item.label}</p> : null}
                  </NavLink>
                ))}
              </div>
            </div>
          </nav>
          <div className="sidebar-footer">
            <a className="sub-link-content sidebar-pro-link" href={config.adminUrl}>
              <span className="sidebar-icon">
                <Settings size={18} aria-hidden="true" />
              </span>
              {!collapsed ? (
                <span className="sidebar-pro-copy">
                  <span className="sidebar-pro-title">Admin</span>
                  <span className="sidebar-pro-subtitle">Catalog control</span>
                </span>
              ) : null}
            </a>
            <a className="sub-link-content" href="/privacy">
              <span className="sidebar-icon">
                <Shield size={18} aria-hidden="true" />
              </span>
              {!collapsed ? <p>Privacy</p> : null}
            </a>
            <button
              type="button"
              className="sidebar-collapse-btn"
              onClick={() => setCollapsed((value) => !value)}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
            </button>
          </div>
        </aside>
        <button type="button" className="sidebar-backdrop" onClick={() => setMobileOpen(false)} aria-label="Close navigation menu" />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<OverviewPage />} />
            <Route path="console" element={<Navigate to="/dashboard" replace />} />
            <Route path="libraries" element={<LibrariesPage />} />
            <Route path="libraries/:vendor/*" element={<LibraryDetailPage />} />
            <Route path="setup" element={<SetupPage />} />
            <Route path="status" element={<StatusPage />} />
            <Route path="settings" element={<AccountPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function OverviewPage() {
  const { data: libraries, loading: librariesLoading } = useAsync(listLibraries, []);
  const { data: status } = useAsync(getStatus, null);
  const totals = useMemo(() => summarizeLibraries(libraries || []), [libraries]);
  const operational = status?.status === "operational";

  return (
    <Page title="Overview" description="Install Oz, sign in from the CLI, and inspect the public documentation catalog.">
      <section className="summary-grid" aria-label="Catalog summary">
        <Metric label="Libraries" value={librariesLoading ? "Loading" : integer(totals.libraries)} icon={Library} />
        <Metric label="Chunks" value={compactNumber(totals.chunks)} icon={FileText} />
        <Metric label="Tokens" value={compactNumber(totals.tokens)} icon={Database} />
        <Metric label="System" value={operational ? "Operational" : "Check status"} icon={operational ? CheckCircle2 : CircleAlert} tone={operational ? "ok" : "warn"} />
      </section>

      <div className="two-column">
        <section className="panel">
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
        </section>
        <section className="panel">
          <SectionHeader title="How agents should use it" />
          <Checklist
            items={[
              "Use oz suggest when the library is unknown.",
              "Use oz pull to materialize docs under .codo/vendors.",
              "Use oz search for semantic path discovery.",
              "Use rg/read/glob on pulled Markdown files for final context.",
              "Use oz prune when local docs need cleanup."
            ]}
          />
        </section>
      </div>

      <section className="panel">
        <SectionHeader title="Recent catalog" action={<Link to="/libraries">Browse all <ChevronRight size={15} /></Link>} />
        <LibraryTable rows={(libraries || []).slice(0, 8)} loading={librariesLoading} compact />
      </section>
    </Page>
  );
}

function LibrariesPage() {
  const { data, loading, error } = useAsync(listLibraries, []);
  const [query, setQuery] = useState("");
  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return data || [];
    }
    return (data || []).filter((row) =>
      [row.vendor, row.library, row.description, row.version].some((value) =>
        String(value || "").toLowerCase().includes(needle)
      )
    );
  }, [data, query]);

  return (
    <Page title="Libraries" description="Public packs available for pull, search, and local agent reading.">
      <div className="toolbar">
        <label className="search-box">
          <Search size={16} aria-hidden="true" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by vendor, library, version, or description" />
        </label>
      </div>
      {error ? <StateMessage tone="warn" title="Catalog unavailable" body={error.message} /> : null}
      <section className="panel flush">
        <LibraryTable rows={rows} loading={loading} />
      </section>
    </Page>
  );
}

function LibraryDetailPage() {
  const params = useParams();
  const vendor = params.vendor || "";
  const library = params["*"] || "";
  const { data, loading, error } = useAsync(() => getLibrary(vendor, library), null, [vendor, library]);

  if (loading) {
    return <Page title="Library" description="Loading pack metadata."><SkeletonRows /></Page>;
  }
  if (error) {
    return <Page title="Library not found" description={error.message}><Link className="button secondary" to="/libraries">Back to libraries</Link></Page>;
  }
  if (!data) {
    return null;
  }

  const id = `${data.vendor}/${data.library}`;
  return (
    <Page title={id} description={data.description || "Versioned documentation pack."}>
      <section className="summary-grid">
        <Metric label="Version" value={data.version || "latest"} icon={Package} />
        <Metric label="Files" value={integer(data.file_count)} icon={BookOpen} />
        <Metric label="Chunks" value={compactNumber(data.chunk_count)} icon={FileText} />
        <Metric label="Tokens" value={compactNumber(data.token_count)} icon={Database} />
      </section>

      <div className="two-column">
        <section className="panel">
          <SectionHeader title="Pull and search" />
          <CommandBlock
            lines={[
              `oz pull ${id}`,
              `oz search "how do I configure this" ${id}`,
              `oz context "show an implementation example" ${id} --max-tokens 1800`,
              `rg "keyword" .codo/vendors/${data.vendor}/${data.library}@${data.version || "latest"}/`
            ]}
          />
        </section>
        <section className="panel">
          <SectionHeader title="Pack metadata" />
          <DefinitionList
            rows={[
              ["Indexed", dateText(data.indexed_at)],
              ["Last crawled", dateText(data.last_crawled_at)],
              ["Pack size", bytes(data.pack_bytes)],
              ["Benchmark", percent(data.benchmark_score)],
              ["Trust", percent(data.trust_score)],
              ["Ref", data.ref_sha || "Not recorded"]
            ]}
          />
        </section>
      </div>

      <div className="two-column">
        <section className="panel">
          <SectionHeader title="Content types" />
          <SimpleTable
            columns={["Type", "Chunks", "Tokens"]}
            rows={(data.content_types || []).map((row) => [row.content_type, integer(row.chunk_count), compactNumber(row.token_count)])}
          />
        </section>
        <section className="panel">
          <SectionHeader title="Versions" />
          <SimpleTable
            columns={["Version", "Chunks", "Indexed"]}
            rows={(data.versions || []).map((row) => [row.version, integer(row.chunk_count), dateText(row.indexed_at)])}
          />
        </section>
      </div>

      <section className="panel">
        <SectionHeader title="Top files" />
        <SimpleTable
          columns={["Path", "Chunks", "Tokens"]}
          rows={(data.top_files || []).map((row) => [row.path, integer(row.chunk_count), compactNumber(row.token_count)])}
        />
      </section>

      <section className="panel">
        <SectionHeader title="Sources" />
        <SimpleTable
          columns={["Source", "Type", "Priority", "Enabled"]}
          rows={(data.sources || []).map((row) => [
            row.source_url ? <a href={row.source_url}>{row.source_url}</a> : "Not recorded",
            row.source_type || "source",
            row.priority ?? "-",
            row.enabled ? "yes" : "no"
          ])}
        />
      </section>
    </Page>
  );
}

function SetupPage() {
  return (
    <Page title="Setup" description="Install the CLI, authenticate once, and let agents use local docs as files.">
      <div className="two-column">
        <section className="panel">
          <SectionHeader title="CLI workflow" />
          <CommandBlock
            lines={[
              "npm install -g @hiringbae/oz",
              "oz login --api-url https://api.tryoz.dev",
              "oz init",
              'oz suggest "react form actions"',
              "oz pull facebook/react",
              'oz search "useEffect cleanup dependency array" facebook/react',
              "oz prune facebook/react"
            ]}
          />
        </section>
        <section className="panel">
          <SectionHeader title="Agent instruction" />
          <CodeBlock>
            {`Use Oz before guessing external library APIs.
Start with: oz search "<query>" [library]
Then read files under .codo/vendors with rg, glob, and read.`}
          </CodeBlock>
        </section>
      </div>

      <section className="panel">
        <SectionHeader title="Path-first MCP" />
        <p className="body-text">
          Oz exposes a small MCP wrapper for clients that prefer native tools. The default tool returns paths and line ranges, not large snippet blobs.
        </p>
        <CodeBlock>
          {`{
  "mcpServers": {
    "oz": {
      "command": "oz",
      "args": ["mcp"],
      "env": {
        "OZ_API_URL": "https://api.tryoz.dev"
      }
    }
  }
}`}
        </CodeBlock>
      </section>

      <section className="panel">
        <SectionHeader title="GitHub Action" />
        <CodeBlock>
          {`- uses: Sricharan07/oz/.github/actions/setup-oz@v0.1.5
  with:
    api-url: https://api.tryoz.dev
    pull: vercel/next.js facebook/react
  env:
    OZ_AUTH_TOKEN: \${{ secrets.OZ_AUTH_TOKEN }}`}
        </CodeBlock>
      </section>
    </Page>
  );
}

function StatusPage() {
  const { data, loading, error } = useAsync(getStatus, null);
  const components = data?.components || {};
  return (
    <Page title="Status" description="Operational view from the public status endpoint.">
      {error ? <StateMessage tone="warn" title="Status unavailable" body={error.message} /> : null}
      {loading ? <SkeletonRows /> : null}
      {data ? (
        <>
          <section className="summary-grid">
            <Metric label="Service" value={data.status} icon={Monitor} tone={data.status === "operational" ? "ok" : "warn"} />
            <Metric label="Libraries" value={integer(components.catalog?.libraries)} icon={Library} />
            <Metric label="Queued crawls" value={integer(components.crawler?.queued)} icon={Activity} />
            <Metric label="Open alerts" value={integer(components.alerts?.open)} icon={CircleAlert} tone={components.alerts?.open ? "warn" : "ok"} />
          </section>
          <section className="panel">
            <SectionHeader title="Components" />
            <SimpleTable
              columns={["Component", "Status"]}
              rows={Object.entries(components).map(([key, value]) => [
                key,
                <span key={key} className={`state ${statusClass(value?.status || (value?.open ? "warn" : "up"))}`}>{value?.status || JSON.stringify(value)}</span>
              ])}
            />
          </section>
        </>
      ) : null}
    </Page>
  );
}

function AccountPage() {
  const config = runtimeConfig();
  return (
    <Page title="Account" description="Use the backend-backed account pages for password, sessions, and device approval.">
      <div className="action-grid">
        <ActionCard title="Sign in" body="Create or resume a web session." href="/sign-in" icon={LogIn} />
        <ActionCard title="Create account" body="Use the public account creation flow." href="/sign-up" icon={UserRound} />
        <ActionCard title="Approve CLI device" body="Enter the device code shown by oz login." href="/device" icon={KeyRound} />
        <ActionCard title="Session settings" body="Change password and revoke CLI sessions." href="/account" icon={Shield} />
        <ActionCard title="Admin" body="Open operator tools for catalog, crawls, and promotions." href={config.adminUrl} icon={Settings} />
      </div>
    </Page>
  );
}

function AuthPage({ mode }) {
  const isSignup = mode === "signup";
  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="brand compact" to="/dashboard">
          <span className="brand-mark">oz</span>
          <span className="brand-text">Console</span>
        </Link>
        <h1>{isSignup ? "Create account" : "Sign in"}</h1>
        <form method="post" action={isSignup ? "/signup" : "/login"} className="auth-form">
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete={isSignup ? "new-password" : "current-password"} minLength={12} required />
          </label>
          {isSignup ? (
            <label>
              Confirm password
              <input name="confirm_password" type="password" autoComplete="new-password" minLength={12} required />
            </label>
          ) : null}
          <button className="button primary wide" type="submit">
            {isSignup ? "Create account" : "Sign in"}
          </button>
        </form>
        <p className="auth-switch">
          {isSignup ? "Already have an account?" : "Need an account?"}{" "}
          <Link to={isSignup ? "/sign-in" : "/sign-up"}>{isSignup ? "Sign in" : "Create one"}</Link>
        </p>
      </section>
    </main>
  );
}

function NotFoundPage() {
  return (
    <Page title="Page not found" description="The console route does not exist.">
      <Link className="button secondary" to="/dashboard">Open overview</Link>
    </Page>
  );
}

function Page({ title, description, children }) {
  return (
    <div className="page">
      <div className="page-header">
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </div>
  );
}

function Metric({ label, value, icon: Icon, tone = "" }) {
  return (
    <div className={`metric ${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <Icon size={18} aria-hidden="true" />
    </div>
  );
}

function SectionHeader({ title, action }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  );
}

function CommandBlock({ lines }) {
  return (
    <CodeBlock>
      {lines.map((line) => `$ ${line}`).join("\n")}
    </CodeBlock>
  );
}

function CodeBlock({ children }) {
  return <pre className="code-block"><code>{children}</code></pre>;
}

function Checklist({ items }) {
  return (
    <ul className="checklist">
      {items.map((item) => (
        <li key={item}>
          <CheckCircle2 size={16} aria-hidden="true" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function LibraryTable({ rows, loading, compact = false }) {
  if (loading) {
    return <SkeletonRows />;
  }
  if (!rows.length) {
    return <StateMessage title="No libraries found" body="Try a different filter or check the catalog endpoint." />;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Library</th>
            <th>Version</th>
            <th>Chunks</th>
            <th>Tokens</th>
            {!compact ? <th>Updated</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.vendor}/${row.library}/${row.version}`}>
              <td>
                <Link className="library-cell" to={libraryPath(row)}>
                  <strong>{libraryId(row)}</strong>
                  <span>{row.description || row.source_url || "Documentation pack"}</span>
                </Link>
              </td>
              <td>{row.version || "latest"}</td>
              <td>{integer(row.chunk_count)}</td>
              <td>{compactNumber(row.token_count)}</td>
              {!compact ? <td>{dateText(row.last_crawled_at || row.indexed_at)}</td> : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SimpleTable({ columns, rows }) {
  if (!rows.length) {
    return <p className="empty-text">No records yet.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DefinitionList({ rows }) {
  return (
    <dl className="definitions">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function ActionCard({ title, body, href, icon: Icon }) {
  return (
    <a className="action-card" href={href}>
      <Icon size={18} aria-hidden="true" />
      <span>
        <strong>{title}</strong>
        <span className="action-body">{body}</span>
      </span>
      <ExternalLink size={15} aria-hidden="true" />
    </a>
  );
}

function StateMessage({ title, body, tone = "" }) {
  return (
    <div className={`state-message ${tone}`}>
      <CircleAlert size={17} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {body ? <span>{body}</span> : null}
      </div>
    </div>
  );
}

function SkeletonRows() {
  return (
    <div className="skeleton-list" aria-label="Loading">
      <span />
      <span />
      <span />
    </div>
  );
}

function useAsync(loader, fallback, deps = []) {
  const [state, setState] = useState({ data: fallback, loading: true, error: null });
  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: null }));
    loader()
      .then((data) => {
        if (active) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (active) {
          setState({ data: fallback, loading: false, error });
        }
      });
    return () => {
      active = false;
    };
    // The caller owns refresh cadence through the explicit dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

function summarizeLibraries(rows) {
  return rows.reduce(
    (totals, row) => ({
      libraries: totals.libraries + 1,
      chunks: totals.chunks + Number(row.chunk_count || 0),
      tokens: totals.tokens + Number(row.token_count || 0)
    }),
    { libraries: 0, chunks: 0, tokens: 0 }
  );
}
