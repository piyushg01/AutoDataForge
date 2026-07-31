export default function AuditView({ audit }) {
  return (
    <div style={{ maxHeight: "420px", overflowY: "auto", border: "1px solid #e2e8f0", borderRadius: "8px", background: "#0f172a", color: "#e2e8f0", padding: "10px", fontFamily: "Consolas, monospace", fontSize: "12px" }}>
      {(audit || []).length ? (audit || []).slice(-120).reverse().map((r, i) => (
        <div key={i} style={{ borderBottom: "1px solid #1e293b", padding: "6px 0" }}>
          <div style={{ color: "#93c5fd" }}>{r.timestamp}</div>
          <div>{r.action || r.operation || "event"} | {(r.current_hash || "").slice(0, 20)}...</div>
        </div>
      )) : <div style={{ color: "#94a3b8" }}>No audit records.</div>}
    </div>
  );
}
