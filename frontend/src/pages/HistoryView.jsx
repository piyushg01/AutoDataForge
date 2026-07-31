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

export default function HistoryView({ history }) {
  return (
    <SimpleTable
      headers={["timestamp", "domain", "model_score"]}
      rows={(history || []).slice(-30).reverse().map((r) => ({
        timestamp: r.timestamp,
        domain: r.domain,
        model_score: r.model_score,
      }))}
    />
  );
}
