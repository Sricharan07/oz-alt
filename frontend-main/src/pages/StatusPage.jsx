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
              rows={Object.entries(components).map(([key, value]) => componentRow(key, value))}
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

function componentRow(key, value) {
  const status = componentStatus(value);
  return [
    key,
    <span key={key} className={`state ${statusClass(status)}`}>
      {componentLabel(key, value)}
    </span>
  ];
}

function componentStatus(value) {
  if (value?.status) {
    return value.status;
  }
  if (typeof value?.open === "number") {
    return value.open > 0 ? "warn" : "up";
  }
  if (typeof value?.fresh_verified === "boolean") {
    return value.fresh_verified ? "up" : "warn";
  }
  return "up";
}

function componentLabel(key, value) {
  if (value?.status) {
    return value.status;
  }
  if (key === "catalog") {
    return `${integer(value?.libraries)} libraries`;
  }
  if (key === "crawler") {
    return `${integer(value?.queued)} queued, ${integer(value?.running)} running`;
  }
  if (key === "alerts") {
    return `${integer(value?.open)} open`;
  }
  if (key === "backups") {
    return value?.fresh_verified ? "verified" : "needs verification";
  }
  return "up";
}
