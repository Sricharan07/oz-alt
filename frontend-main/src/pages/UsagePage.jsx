import { LineChart, Package, Search, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Metric, Page, Panel, SectionHeader, SimpleTable, SkeletonRows, StateMessage } from "../components/ui/index.js";
import { dateText, integer } from "../format.js";
import { useConsoleAccount } from "../hooks/useConsoleAccount.js";
import { useMotionProgress } from "../hooks/useMotionProgress.js";

export function UsagePage() {
  const account = useConsoleAccount();

  if (account.loading) {
    return (
      <Page title="Usage" description="Loading account usage.">
        <SkeletonRows />
      </Page>
    );
  }

  if (account.error) {
    return (
      <Page title="Usage" description="Unable to load usage.">
        <StateMessage tone="warn" title="Usage unavailable" body={account.error.message} />
      </Page>
    );
  }

  if (!account.authenticated) {
    return (
      <Page title="Usage" description="Sign in to see search, pull, and CLI activity.">
        <StateMessage title="Account required" body="Usage is tied to your Oz account and CLI sessions." />
        <Link className="button primary" to="/sign-in">Sign in</Link>
      </Page>
    );
  }

  const totals = account.usage?.totals || {};
  const daily = account.usage?.daily || [];
  const recent = account.usage?.recent_events || [];

  return (
    <Page title="Usage" description="Account-level activity from CLI search, suggest, pull, and context requests.">
      <section className="summary-grid">
        <Metric label="Events" value={integer(totals.events)} icon={LineChart} />
        <Metric label="Searches" value={integer(totals.searches)} icon={Search} />
        <Metric label="Pulls" value={integer(totals.pulls)} icon={Package} />
        <Metric label="Suggestions" value={integer(totals.suggests)} icon={Sparkles} />
      </section>

      <UsageBars rows={daily} />

      <div className="two-column">
        <Panel>
          <SectionHeader title="Top activity" />
          <SimpleTable
            columns={["Event", "Library", "Count"]}
            rows={(account.usage?.summary || []).map((row) => [
              row.event,
              row.library || "All libraries",
              integer(row.count)
            ])}
          />
        </Panel>
        <Panel>
          <SectionHeader title="Recent events" />
          <SimpleTable
            columns={["Event", "Library", "Results", "Created"]}
            rows={recent.map((row) => [
              row.event,
              row.library || "-",
              row.result_count ?? "-",
              dateText(row.created_at)
            ])}
          />
        </Panel>
      </div>
    </Page>
  );
}

function UsageBars({ rows }) {
  const grouped = groupDailyUsage(rows);
  const progress = useMotionProgress(grouped.map((row) => `${row.day}:${row.count}`).join("|"));
  const max = Math.max(...grouped.map((row) => row.count), 1);

  return (
    <Panel className="usage-panel">
      <SectionHeader title="Last 30 days" />
      {grouped.length ? (
        <>
          <div className="usage-bars" aria-label="Daily usage chart">
            {grouped.map((row) => {
              const height = Math.max(8, Math.round((row.count / max) * 100 * progress));
              return (
                <div
                  key={row.day}
                  className="usage-bar"
                  style={{ height: `${height}%` }}
                  data-tooltip={`${row.day}: ${integer(row.count)} events`}
                />
              );
            })}
          </div>
          <div className="overview-chart-labels">
            <span>oldest</span>
            <span>daily account activity</span>
            <span>latest</span>
          </div>
        </>
      ) : (
        <p className="empty-text">No usage has been recorded for this account yet.</p>
      )}
    </Panel>
  );
}

function groupDailyUsage(rows) {
  const byDay = new Map();
  for (const row of rows || []) {
    const day = String(row.day || "").slice(0, 10);
    if (!day) {
      continue;
    }
    byDay.set(day, (byDay.get(day) || 0) + Number(row.count || 0));
  }
  return [...byDay.entries()]
    .map(([day, count]) => ({ day, count }))
    .sort((a, b) => a.day.localeCompare(b.day))
    .slice(-30);
}
