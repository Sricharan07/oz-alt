import { KeyRound, LogIn, RefreshCw, Settings, Shield, UserRound } from "lucide-react";
import { useState } from "react";
import { runtimeConfig } from "../config.js";
import {
  ActionCard,
  Metric,
  Page,
  Panel,
  SectionHeader,
  SimpleTable,
  SkeletonRows,
  StateMessage
} from "../components/ui/index.js";
import { dateText, integer } from "../format.js";
import { useConsoleAccount } from "../hooks/useConsoleAccount.js";

export function AccountPage() {
  const config = runtimeConfig();
  const account = useConsoleAccount();

  if (account.loading) {
    return (
      <Page title="Account" description="Loading session state.">
        <SkeletonRows />
      </Page>
    );
  }

  if (account.error) {
    return (
      <Page title="Account" description="Unable to load your account state.">
        <StateMessage tone="warn" title="Account unavailable" body={account.error.message} />
      </Page>
    );
  }

  if (!account.authenticated) {
    return (
      <Page title="Account" description="Sign in to manage CLI devices, web sessions, and usage.">
        <div className="action-grid">
          <ActionCard title="Sign in" body="Resume your Oz web session." href="/sign-in" icon={LogIn} />
          <ActionCard title="Create account" body="Create a console account for CLI login." href="/sign-up" icon={UserRound} />
          <ActionCard title="Approve CLI device" body="Sign in first, then enter the code from oz login." href="/device" icon={KeyRound} />
          <ActionCard title="Status" body="Check public service status without signing in." href="/status" icon={Shield} />
        </div>
      </Page>
    );
  }

  const totals = account.usage?.totals || {};

  return (
    <Page
      title="Account"
      description={`${account.user.email} · ${account.user.role}`}
      actions={
        <button className="button secondary" type="button" onClick={() => void account.refresh()}>
          <RefreshCw size={15} aria-hidden="true" />
          Refresh
        </button>
      }
    >
      <section className="summary-grid">
        <Metric label="Searches" value={integer(totals.searches)} icon={LogIn} />
        <Metric label="Pulls" value={integer(totals.pulls)} icon={KeyRound} />
        <Metric label="Suggestions" value={integer(totals.suggests)} icon={UserRound} />
        <Metric label="Libraries used" value={integer(totals.libraries)} icon={Shield} />
      </section>

      <div className="two-column">
        <Panel>
          <SectionHeader title="CLI sessions" action={<a href="/device">Approve device</a>} />
          <SessionTable
            rows={account.cliSessions}
            empty="No CLI sessions yet."
            columns={["Machine", "Created", "Last used", "Status", ""]}
            row={(session) => [
              session.machine_id || "Unknown machine",
              dateText(session.created_at),
              dateText(session.last_used_at),
              session.revoked_at ? "Revoked" : "Active",
              session.revoked_at ? "" : (
                <button className="button secondary compact" type="button" onClick={() => void account.revokeCli(session.id)}>
                  Revoke
                </button>
              )
            ]}
          />
        </Panel>

        <Panel>
          <SectionHeader title="Web sessions" action={<button className="inline-action" type="button" onClick={() => void account.logout()}>Logout</button>} />
          <SessionTable
            rows={account.webSessions}
            empty="No web sessions found."
            columns={["Session", "Created", "Expires", "Status", ""]}
            row={(session) => [
              session.current ? "Current browser" : "Browser session",
              dateText(session.created_at),
              dateText(session.expires_at),
              session.revoked_at ? "Revoked" : session.current ? "Current" : "Active",
              session.revoked_at || session.current ? "" : (
                <button className="button secondary compact" type="button" onClick={() => void account.revokeWeb(session.id)}>
                  Revoke
                </button>
              )
            ]}
          />
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="Usage summary" />
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
        <SectionHeader title="Recent activity" />
        <SimpleTable
          columns={["Event", "Library", "Query length", "Results", "Created"]}
          rows={(account.usage?.recent_events || []).map((row) => [
            row.event,
            row.library || "-",
            row.query_length ?? "-",
            row.result_count ?? "-",
            dateText(row.created_at)
          ])}
        />
      </Panel>

      <PasswordPanel account={account} />

      <div className="action-grid">
        <ActionCard title="Approve CLI device" body="Enter the device code shown by oz login." href="/device" icon={KeyRound} />
        <ActionCard title="Password settings" body="Use backend-protected account settings." href="/account" icon={Shield} />
        {account.user.is_admin ? (
          <ActionCard title="Admin" body="Open catalog, crawl, and promotion controls." href={config.adminUrl} icon={Settings} />
        ) : null}
      </div>
    </Page>
  );
}

function PasswordPanel({ account }) {
  const [form, setForm] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [state, setState] = useState({ loading: false, error: "", message: "" });

  async function submit(event) {
    event.preventDefault();
    setState({ loading: true, error: "", message: "" });
    try {
      await account.changePassword(form);
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      setState({ loading: false, error: "", message: "Password updated." });
    } catch (error) {
      setState({ loading: false, error: error.message || "Unable to update password.", message: "" });
    }
  }

  function update(name) {
    return (event) => setForm((current) => ({ ...current, [name]: event.target.value }));
  }

  return (
    <Panel>
      <SectionHeader title="Password" />
      <form className="settings-form" onSubmit={submit}>
        <label>
          Current password
          <input value={form.currentPassword} onChange={update("currentPassword")} type="password" autoComplete="current-password" required />
        </label>
        <label>
          New password
          <input value={form.newPassword} onChange={update("newPassword")} type="password" autoComplete="new-password" minLength={12} required />
        </label>
        <label>
          Confirm new password
          <input value={form.confirmPassword} onChange={update("confirmPassword")} type="password" autoComplete="new-password" minLength={12} required />
        </label>
        {state.error ? <StateMessage tone="warn" title="Password update failed" body={state.error} /> : null}
        {state.message ? <StateMessage title="Password updated" body={state.message} /> : null}
        <button className="button primary" type="submit" disabled={state.loading}>
          {state.loading ? "Updating..." : "Update password"}
        </button>
      </form>
    </Panel>
  );
}

function SessionTable({ rows, empty, columns, row }) {
  if (!rows.length) {
    return <p className="empty-text">{empty}</p>;
  }
  return <SimpleTable columns={columns} rows={rows.map(row)} />;
}
