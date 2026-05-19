import { Activity, CircleAlert, Library, Monitor } from "lucide-react";
import { getStatus } from "../api.js";
import { Metric, Page, Panel, SectionHeader, SimpleTable, SkeletonRows, StateMessage } from "../components/ui/index.js";
import { integer, statusClass } from "../format.js";
import { useAsync } from "../hooks/useAsync.js";

export function StatusPage() {
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
          <Panel>
            <SectionHeader title="Components" />
            <SimpleTable
              columns={["Component", "Status"]}
              rows={Object.entries(components).map(([key, value]) => [
                key,
                <span key={key} className={`state ${statusClass(value?.status || (value?.open ? "warn" : "up"))}`}>
                  {value?.status || JSON.stringify(value)}
                </span>
              ])}
            />
          </Panel>
          <Panel>
            <SectionHeader title="Readiness" />
            <SimpleTable
              columns={["Area", "Expected state"]}
              rows={[
                ["API", "Healthy and reachable"],
                ["Catalog", "Promoted libraries visible"],
                ["Crawler", "No stuck queue"],
                ["Alerts", "No unresolved incidents"]
              ]}
            />
          </Panel>
        </>
      ) : null}
    </Page>
  );
}
