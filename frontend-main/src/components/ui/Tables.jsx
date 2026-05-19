import { Link } from "react-router-dom";
import { compactNumber, dateText, integer, libraryId, libraryPath } from "../../format.js";
import { StateMessage, SkeletonRows } from "./Blocks.jsx";

export function LibraryTable({ rows, loading, compact = false }) {
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

export function SimpleTable({ columns, rows }) {
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

export function DefinitionList({ rows }) {
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
