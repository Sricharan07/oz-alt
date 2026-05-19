import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { listLibraries } from "../api.js";
import { LibraryTable, Page, Panel, StateMessage } from "../components/ui/index.js";
import { useAsync } from "../hooks/useAsync.js";

export function LibrariesPage() {
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
    <Page title="Libraries" description="Public packs available for pull, search, context, and local agent reading.">
      <div className="toolbar">
        <label className="search-box">
          <Search size={16} aria-hidden="true" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by vendor, library, version, or description" />
        </label>
      </div>
      {error ? <StateMessage tone="warn" title="Catalog unavailable" body={error.message} /> : null}
      <Panel flush>
        <LibraryTable rows={rows} loading={loading} />
      </Panel>
    </Page>
  );
}
