export function summarizeLibraries(rows) {
  return rows.reduce(
    (totals, row) => ({
      libraries: totals.libraries + 1,
      chunks: totals.chunks + Number(row.chunk_count || 0),
      tokens: totals.tokens + Number(row.token_count || 0)
    }),
    { libraries: 0, chunks: 0, tokens: 0 }
  );
}

export function topLibraries(rows, limit = 7) {
  return [...rows]
    .sort((a, b) => Number(b.chunk_count || 0) - Number(a.chunk_count || 0))
    .slice(0, limit);
}
