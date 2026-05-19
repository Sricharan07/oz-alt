import { KeyRound, Laptop, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { approveDeviceCode } from "../api.js";
import { Checklist, CommandBlock, Metric, Page, Panel, SectionHeader, StateMessage } from "../components/ui/index.js";
import { dateText, integer } from "../format.js";
import { useConsoleAccount } from "../hooks/useConsoleAccount.js";
import { useToast } from "../hooks/useToast.js";

export function DevicePage() {
  const [params] = useSearchParams();
  const initialCode = params.get("code") || "";
  const account = useConsoleAccount();
  const { notify } = useToast();
  const [code, setCode] = useState(formatCode(initialCode));
  const [state, setState] = useState({ loading: false, error: "", done: false });

  const activeSessions = useMemo(
    () => account.cliSessions.filter((session) => !session.revoked_at),
    [account.cliSessions]
  );

  async function submit(event) {
    event.preventDefault();
    setState({ loading: true, error: "", done: false });
    try {
      await approveDeviceCode(code, account.data?.csrf || "");
      await account.refresh();
      setState({ loading: false, error: "", done: true });
      notify({ tone: "success", title: "Device approved", message: "Return to your terminal to finish oz login." });
    } catch (error) {
      setState({ loading: false, error: error.message || "Unable to approve device.", done: false });
      notify({ tone: "warning", title: "Approval failed", message: error.message || "Check the code and try again." });
    }
  }

  if (account.loading) {
    return (
      <Page title="Approve device" description="Loading your account session.">
        <Panel>
          <p className="empty-text">Checking session…</p>
        </Panel>
      </Page>
    );
  }

  if (!account.authenticated) {
    return (
      <Page title="Approve device" description="Sign in with the same account you use from the CLI.">
        <StateMessage title="Account required" body="Run oz login, then sign in here and enter the device code shown in your terminal." />
        <div className="action-row">
          <Link className="button primary" to={`/sign-in${code ? `?next=/device?code=${encodeURIComponent(code)}` : ""}`}>Sign in</Link>
          <Link className="button secondary" to="/setup">Setup guide</Link>
        </div>
      </Page>
    );
  }

  return (
    <Page
      title="Approve device"
      description="Connect a CLI install to this account without copying long-lived credentials."
    >
      <section className="summary-grid">
        <Metric label="Signed in" value={account.user.email} icon={ShieldCheck} />
        <Metric label="CLI sessions" value={integer(activeSessions.length)} icon={Laptop} />
        <Metric label="Last session" value={dateText(activeSessions[0]?.last_used_at || activeSessions[0]?.created_at)} icon={KeyRound} />
        <Metric label="Flow" value="Device code" icon={ShieldCheck} tone="ok" />
      </section>

      <div className="two-column">
        <Panel>
          <SectionHeader title="Enter code" />
          <form className="device-form" onSubmit={submit}>
            <label>
              Device code
              <input
                value={code}
                onChange={(event) => setCode(formatCode(event.target.value))}
                placeholder="ABCD-EFGH"
                autoComplete="one-time-code"
                spellCheck="false"
                required
              />
            </label>
            {state.error ? <StateMessage tone="warn" title="Device approval failed" body={state.error} /> : null}
            {state.done ? <StateMessage title="Device approved" body="The CLI can now exchange the device token." /> : null}
            <button className="button primary" type="submit" disabled={state.loading || code.length < 4}>
              {state.loading ? "Approving…" : "Approve device"}
            </button>
          </form>
        </Panel>

        <Panel>
          <SectionHeader title="Start from terminal" />
          <CommandBlock
            lines={[
              "npm install -g @hiringbae/oz",
              "oz login --api-url https://api.tryoz.dev"
            ]}
          />
          <Checklist
            items={[
              "Use the browser account you want usage tracked against.",
              "Device codes expire quickly and cannot be reused.",
              "You can revoke CLI sessions from Account at any time."
            ]}
          />
        </Panel>
      </div>
    </Page>
  );
}

function formatCode(value) {
  const normalized = String(value || "")
    .replace(/[^a-z0-9]/gi, "")
    .slice(0, 8)
    .toUpperCase();
  if (normalized.length <= 4) {
    return normalized;
  }
  return `${normalized.slice(0, 4)}-${normalized.slice(4)}`;
}
