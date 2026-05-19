import { BookOpen, Database, FileText, Package } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { getLibrary } from "../api.js";
import {
  CommandBlock,
  DefinitionList,
  Metric,
  Page,
  Panel,
  SectionHeader,
  SimpleTable,
  SkeletonRows
} from "../components/ui/index.js";
import { bytes, compactNumber, dateText, integer, percent } from "../format.js";
import { useAsync } from "../hooks/useAsync.js";

export function LibraryDetailPage() {
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
  const vendorPath = `.codo/vendors/${data.vendor}/${data.library}@${data.version || "latest"}/`;

  return (
    <Page title={id} description={data.description || "Versioned documentation pack."}>
      <section className="summary-grid">
        <Metric label="Version" value={data.version || "latest"} icon={Package} />
        <Metric label="Files" value={integer(data.file_count)} icon={BookOpen} />
        <Metric label="Chunks" value={compactNumber(data.chunk_count)} icon={FileText} />
        <Metric label="Tokens" value={compactNumber(data.token_count)} icon={Database} />
      </section>

      <div className="two-column">
        <Panel>
          <SectionHeader title="Pull and search" />
          <CommandBlock
            lines={[
              `oz pull ${id}`,
              `oz search "how do I configure this" ${id}`,
              `oz context "show an implementation example" ${id} --max-tokens 1800`,
              `rg "keyword" ${vendorPath}`
            ]}
          />
        </Panel>
        <Panel>
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
        </Panel>
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="Content types" />
          <SimpleTable
            columns={["Type", "Chunks", "Tokens"]}
            rows={(data.content_types || []).map((row) => [row.content_type, integer(row.chunk_count), compactNumber(row.token_count)])}
          />
        </Panel>
        <Panel>
          <SectionHeader title="Versions" />
          <SimpleTable
            columns={["Version", "Chunks", "Indexed"]}
            rows={(data.versions || []).map((row) => [row.version, integer(row.chunk_count), dateText(row.indexed_at)])}
          />
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="Top files" />
        <SimpleTable
          columns={["Path", "Chunks", "Tokens"]}
          rows={(data.top_files || []).map((row) => [row.path, integer(row.chunk_count), compactNumber(row.token_count)])}
        />
      </Panel>

      <Panel>
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
      </Panel>
    </Page>
  );
}
