import { ArrowDownAZ, Blocks, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { listLibraries } from "../api.js";
import { LibraryTable, Metric, Page, Panel, StateMessage } from "../components/ui/index.js";
import { compactNumber, integer } from "../format.js";
import { useAsync } from "../hooks/useAsync.js";
import { summarizeLibraries } from "./pageData.js";

export function LibrariesPage() {
  const { data, loading, error } = useAsync(listLibraries, []);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("usage");
  const [vendor, setVendor] = useState("all");
  const totals = useMemo(() => summarizeLibraries(data || []), [data]);
  const vendors = useMemo(() => {
    const names = [...new Set((data || []).map((row) => row.vendor).filter(Boolean))].sort();
    return ["all", ...names];
  }, [data]);
  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    let filtered = data || [];
    if (vendor !== "all") {
      filtered = filtered.filter((row) => row.vendor === vendor);
    }
    if (needle) {
      filtered = filtered.filter((row) =>
        [row.vendor, row.library, row.description, row.version].some((value) =>
          String(value || "").toLowerCase().includes(needle)
        )
      );
    }
    return [...filtered].sort((a, b) => compareLibraryRows(a, b, sort));
  }, [data, query, sort, vendor]);

  return (
    <Page title="Libraries" description="Public packs available for pull, search, context, and local agent reading.">
      <section className="summary-grid">
        <Metric label="Libraries" value={integer(totals.libraries)} icon={Blocks} />
        <Metric label="Chunks" value={compactNumber(totals.chunks)} icon={Blocks} />
        <Metric label="Tokens" value={compactNumber(totals.tokens)} icon={Blocks} />
        <Metric label="Visible" value={loading ? "Loading" : integer(rows.length)} icon={ArrowDownAZ} />
      </section>

      <div className="toolbar library-toolbar">
        <label className="search-box">
          <Search size={16} aria-hidden="true" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by vendor, library, version, or description" />
        </label>
        <div className="control-row">
          <label>
            Vendor
            <select value={vendor} onChange={(event) => setVendor(event.target.value)}>
              {vendors.map((name) => <option key={name} value={name}>{name === "all" ? "All vendors" : name}</option>)}
            </select>
          </label>
          <label>
            Sort
            <select value={sort} onChange={(event) => setSort(event.target.value)}>
              <option value="usage">Most indexed</option>
              <option value="recent">Recently crawled</option>
              <option value="name">Name</option>
            </select>
          </label>
        </div>
      </div>
      {error ? <StateMessage tone="warn" title="Catalog unavailable" body={error.message} /> : null}
      <Panel flush>
        <LibraryTable rows={rows} loading={loading} />
      </Panel>
    </Page>
  );
}

function compareLibraryRows(a, b, sort) {
  if (sort === "name") {
    return `${a.vendor}/${a.library}`.localeCompare(`${b.vendor}/${b.library}`);
  }
  if (sort === "recent") {
    return Date.parse(b.last_crawled_at || b.indexed_at || 0) - Date.parse(a.last_crawled_at || a.indexed_at || 0);
  }
  return Number(b.chunk_count || 0) - Number(a.chunk_count || 0);
}
