export default function VersionsView({ versions }) {
  return (
    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
      {(versions?.available || []).map((v) => (
        <span key={v} style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "999px", background: "#e2e8f0", color: "#334155" }}>{v}</span>
      ))}
    </div>
  );
}
