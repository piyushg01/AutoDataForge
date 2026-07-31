const ACTION_COLOR = {
  remove: "#fef2f2",
  keep: "#f0fdf4",
  target: "#eff6ff",
};

function actionBadge(action = "") {
  const lower = action.toLowerCase();
  if (lower.includes("remove")) return { bg: "#fee2e2", color: "#dc2626" };
  if (lower.includes("target")) return { bg: "#dbeafe", color: "#1d4ed8" };
  return { bg: "#dcfce7", color: "#16a34a" };
}

const ENCODING_BADGE = {
  LabelEncoding: "#fef9c3",
  OrdinalEncoding: "#fce7f3",
  OneHotEncoding: "#dbeafe",
  BinaryHashEncoding: "#f3e8ff",
  DateFeatureExtraction: "#fff7ed",
  None: "#f1f5f9",
};

export default function CleaningSuggestionPage({ suggestions = [], selectedDrops = [], onToggleDrop }) {
  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
      <h2 style={{ marginTop: 0 }}>Step 4: AI + Rule-Based Column Analysis</h2>
      <p style={{ color: "#475569", marginBottom: "12px" }}>
        The AI engine has analyzed each column and selected encoding, scaling, and outlier methods automatically.
        Uncheck any removal to keep a column.
      </p>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["Column", "Type", "Missing%", "Unique", "Skewness", "Encoding", "Scaling", "Outlier Method", "Action", "Reason", "Remove?"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "8px 10px", borderBottom: "2px solid #e2e8f0", color: "#474969", whiteSpace: "nowrap" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {suggestions.map((item) => {
              const removable = String(item.action || "").toLowerCase().includes("remove");
              const checked = selectedDrops.includes(item.column);
              const { bg, color } = actionBadge(item.action);
              const encBg = ENCODING_BADGE[item.suggested_encoding] || "#f1f5f9";

              return (
                <tr key={item.column} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "7px 10px", fontWeight: 600 }}>{item.column}</td>
                  <td style={{ padding: "7px 10px" }}>
                    <span style={{ fontSize: "11px", padding: "2px 7px", borderRadius: "99px", background: "#f1f5f9", color: "#475569" }}>
                      {item.detected_type}
                    </span>
                  </td>
                  <td style={{ padding: "7px 10px", color: item.missing_pct > 20 ? "#dc2626" : item.missing_pct > 5 ? "#d97706" : "#16a34a" }}>
                    {item.missing_pct}%
                  </td>
                  <td style={{ padding: "7px 10px" }}>{item.unique_values}</td>
                  <td style={{ padding: "7px 10px", color: "#6b7280" }}>
                    {item.skewness != null ? item.skewness : "–"}
                  </td>
                  <td style={{ padding: "7px 10px" }}>
                    {item.suggested_encoding !== "None" ? (
                      <span style={{ fontSize: "11px", padding: "2px 7px", borderRadius: "99px", background: encBg, color: "#374151", whiteSpace: "nowrap" }}>
                        {item.suggested_encoding}
                      </span>
                    ) : <span style={{ color: "#94a3b8" }}>–</span>}
                  </td>
                  <td style={{ padding: "7px 10px", color: "#374151", whiteSpace: "nowrap" }}>
                    {item.scaling !== "None" ? item.scaling : <span style={{ color: "#94a3b8" }}>–</span>}
                  </td>
                  <td style={{ padding: "7px 10px", color: "#374151", whiteSpace: "nowrap" }}>
                    {item.outlier_method && item.outlier_method !== "None"
                      ? <span style={{ fontSize: "11px", padding: "2px 7px", borderRadius: "99px", background: "#fff7ed", color: "#92400e" }}>{item.outlier_method}</span>
                      : <span style={{ color: "#94a3b8" }}>–</span>}
                  </td>
                  <td style={{ padding: "7px 10px" }}>
                    <span style={{ fontSize: "11px", padding: "2px 9px", borderRadius: "99px", background: bg, color, fontWeight: 600, whiteSpace: "nowrap" }}>
                      {item.action}
                    </span>
                  </td>
                  <td style={{ padding: "7px 10px", maxWidth: "200px", color: "#475569", fontSize: "12px" }}>
                    {item.reason || "–"}
                  </td>
                  <td style={{ padding: "7px 10px", textAlign: "center" }}>
                    <input
                      type="checkbox"
                      disabled={!removable}
                      checked={checked}
                      onChange={() => onToggleDrop(item.column)}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {selectedDrops.length > 0 && (
        <div style={{ marginTop: "10px", padding: "10px 14px", background: "#fef2f2", borderRadius: "8px", border: "1px solid #fecaca" }}>
          <strong style={{ color: "#b91c1c" }}>Columns marked for removal ({selectedDrops.length}):</strong>{" "}
          <span style={{ color: "#dc2626" }}>{selectedDrops.join(", ")}</span>
        </div>
      )}
    </section>
  );
}
