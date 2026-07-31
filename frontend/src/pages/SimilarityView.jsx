function SimpleTable({ headers, rows }) {
  if (!rows?.length) return <p style={{ color: "#64748b" }}>No data available.</p>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", background: "#fff" }}>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} style={{ textAlign: "left", padding: "8px 10px", borderBottom: "1px solid #e2e8f0", color: "#475569", background: "#f8fafc" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {headers.map((h) => (
                <td key={h} style={{ padding: "8px 10px", borderBottom: "1px solid #f1f5f9", color: "#334155" }}>{String(row[h] ?? "-")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SimilarityView({ similarity }) {
  const rows = Array.isArray(similarity) ? similarity : [];
  const uniqueTopFive = Object.values(
    rows.reduce((acc, row, index) => {
      const datasetId = String(row?.dataset_id || `__unknown_${index}`);
      const score = Number(row?.similarity || 0);
      if (!acc[datasetId] || score > Number(acc[datasetId]?.similarity || 0)) {
        acc[datasetId] = row;
      }
      return acc;
    }, {})
  )
    .sort((a, b) => Number(b?.similarity || 0) - Number(a?.similarity || 0))
    .slice(0, 5);

  return (
    <SimpleTable
      headers={["dataset_id", "similarity", "target_type", "num_rows", "num_columns", "missing_percentage"]}
      rows={uniqueTopFive.map((r) => ({
        dataset_id: r.dataset_id,
        similarity: Number(r?.similarity || 0).toFixed(4),
        target_type: r?.fingerprint?.target_type,
        num_rows: r?.num_rows ?? r?.fingerprint?.num_rows,
        num_columns: r?.num_columns ?? r?.fingerprint?.num_columns,
        missing_percentage: r?.missing_percentage ?? r?.fingerprint?.missing_percentage,
      }))}
    />
  );
}
