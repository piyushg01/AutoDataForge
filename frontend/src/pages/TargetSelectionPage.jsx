import { useMemo, useState } from "react";

export default function TargetSelectionPage({ columns = [], onSelectTarget }) {
  const [targetColumn, setTargetColumn] = useState("");
  const [problemType, setProblemType] = useState("classification");

  const selectableColumns = useMemo(() => columns || [], [columns]);

  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
      <h2 style={{ marginTop: 0 }}>Step 3: Target Column Selection</h2>
      <div style={{ display: "grid", gap: "12px", maxWidth: "520px" }}>
        <select
          value={targetColumn}
          onChange={(event) => setTargetColumn(event.target.value)}
          style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
        >
          <option value="">Select target column</option>
          {selectableColumns.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))}
        </select>

        <select
          value={problemType}
          onChange={(event) => setProblemType(event.target.value)}
          style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
        >
          <option value="classification">Classification</option>
          <option value="regression">Regression</option>
        </select>

        <button
          type="button"
          disabled={!targetColumn}
          onClick={() => onSelectTarget({ targetColumn, problemType })}
          style={{
            width: "fit-content",
            padding: "10px 16px",
            border: "none",
            borderRadius: "8px",
            background: "linear-gradient(90deg, #2563eb, #0284c7)",
            color: "white",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Confirm Target & Problem Type
        </button>
      </div>
    </section>
  );
}
