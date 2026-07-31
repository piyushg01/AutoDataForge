import { getDownloadUrl } from "../services/api";

function Section({ title, children }) {
  return (
    <div style={{ marginTop: "16px", border: "1px solid #e2e8f0", borderRadius: "10px", overflow: "hidden" }}>
      <div style={{ padding: "8px 14px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", fontWeight: 700, fontSize: "13px", color: "#374151" }}>
        {title}
      </div>
      <div style={{ padding: "12px 14px" }}>{children}</div>
    </div>
  );
}

function Badge({ label, value, bg = "#f1f5f9", color = "#374151" }) {
  return (
    <span style={{ display: "inline-flex", gap: "6px", alignItems: "center", padding: "3px 10px", borderRadius: "99px", background: bg, color, fontSize: "12px", fontWeight: 600, marginRight: "6px", marginBottom: "4px" }}>
      <span style={{ opacity: 0.65 }}>{label}:</span> {value}
    </span>
  );
}

function KVTable({ data, keyLabel = "Column", valLabel = "Value" }) {
  const entries = Object.entries(data || {});
  if (!entries.length) return <span style={{ color: "#94a3b8" }}>None</span>;
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: "5px 8px", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>{keyLabel}</th>
          <th style={{ textAlign: "left", padding: "5px 8px", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>{valLabel}</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([k, v]) => (
          <tr key={k}>
            <td style={{ padding: "5px 8px", borderBottom: "1px solid #f8fafc", fontWeight: 500 }}>{k}</td>
            <td style={{ padding: "5px 8px", borderBottom: "1px solid #f8fafc", color: "#374151" }}>{String(v)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function CleanedDatasetPreview({ cleanedResult }) {
  if (!cleanedResult) {
    return (
      <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
        <h2 style={{ marginTop: 0 }}>Step 6: Cleaned Dataset Preview & Report</h2>
        <p>Run cleaning to preview updated dataset and download cleaned_dataset.csv.</p>
      </section>
    );
  }

  const previewRows = cleanedResult.cleaned_preview || [];
  const headers = previewRows.length ? Object.keys(previewRows[0]) : [];
  const featureImportances = cleanedResult.feature_selection?.feature_importances || {};
  const miScores = cleanedResult.feature_selection?.mutual_info_scores || {};
  const outlierReport = cleanedResult.outlier_report || {};
  const scalerDecisions = cleanedResult.scaler_decisions || {};
  const encDecisions = cleanedResult.encoding_decisions || {};
  const missingActions = cleanedResult.missing_actions || {};
  const discReport = cleanedResult.discretization?.discretized || {};
  const dimReport = cleanedResult.dim_reduction || {};
  const featureDropped = cleanedResult.feature_selection?.dropped || {};

  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
      <h2 style={{ marginTop: 0 }}>Step 6: Cleaned Dataset Preview & Report</h2>

      {/* Summary metrics */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "8px" }}>
        <Badge label="Rows" value={cleanedResult.rows} bg="#dbeafe" color="#1d4ed8" />
        <Badge label="Columns" value={cleanedResult.columns} bg="#dbeafe" color="#1d4ed8" />
        <Badge label="Target" value={cleanedResult.target_column} bg="#dcfce7" color="#16a34a" />
        <Badge label="Problem" value={cleanedResult.problem_type} bg="#f0fdf4" color="#16a34a" />
        <Badge label="Duplicates removed" value={cleanedResult.duplicates_removed} bg="#f1f5f9" />
        <Badge label="Outliers capped" value={cleanedResult.outliers_capped} bg="#fff7ed" color="#92400e" />
        <Badge label="Scaler" value={cleanedResult.scaler} bg="#fef9c3" color="#92400e" />
      </div>

      <div style={{ marginBottom: "10px" }}>
        <a
          href={getDownloadUrl(cleanedResult.download_urls?.cleaned || "/api/download/phase1/cleaned")}
          target="_blank"
          rel="noreferrer"
          style={{
            display: "inline-block", padding: "8px 16px", borderRadius: "8px",
            background: "linear-gradient(90deg,#16a34a,#059669)", color: "white",
            fontWeight: 700, textDecoration: "none", fontSize: "13px",
          }}
        >
          Download cleaned_dataset.csv
        </a>
      </div>

      <>

      {/* Missing value actions */}
      <Section title="Missing Value Handling">
        {Object.keys(missingActions).length ? (
          <KVTable data={missingActions} keyLabel="Column" valLabel="Strategy" />
        ) : <span style={{ color: "#16a34a", fontSize: "13px" }}>No missing values found.</span>}
      </Section>

      {/* Outlier report */}
      <Section title="Outlier Handling (Per-column)">
        {Object.keys(outlierReport).length ? (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr>
                {["Column", "Method", "Outliers Capped"].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "5px 8px", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(outlierReport).map(([col, info]) => (
                <tr key={col}>
                  <td style={{ padding: "5px 8px", fontWeight: 500, borderBottom: "1px solid #f8fafc" }}>{col}</td>
                  <td style={{ padding: "5px 8px", borderBottom: "1px solid #f8fafc" }}>
                    <span style={{ fontSize: "11px", padding: "2px 7px", borderRadius: "99px", background: "#fff7ed", color: "#92400e" }}>{info.method}</span>
                  </td>
                  <td style={{ padding: "5px 8px", borderBottom: "1px solid #f8fafc", color: info.outliers_found > 0 ? "#dc2626" : "#16a34a" }}>
                    {info.outliers_found}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <span style={{ color: "#94a3b8", fontSize: "13px" }}>No outliers detected or no numeric columns.</span>}
      </Section>

      {/* Encoding decisions */}
      <Section title="Encoding Decisions">
        {Object.keys(encDecisions).length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {Object.entries(encDecisions).map(([col, enc]) => (
              <span key={col} style={{ fontSize: "12px", padding: "3px 9px", borderRadius: "99px", background: "#eff6ff", color: "#1d4ed8", fontWeight: 500 }}>
                {col} → {enc}
              </span>
            ))}
          </div>
        ) : <span style={{ color: "#94a3b8" }}>No categorical columns encoded.</span>}
      </Section>

      {/* Scaling decisions */}
      <Section title="Scaling Decisions (Per-column)">
        {Object.keys(scalerDecisions).length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {Object.entries(scalerDecisions).map(([col, scaler]) => (
              <span key={col} style={{ fontSize: "12px", padding: "3px 9px", borderRadius: "99px", background: "#fef9c3", color: "#92400e", fontWeight: 500 }}>
                {col} → {scaler}
              </span>
            ))}
          </div>
        ) : <span style={{ color: "#94a3b8" }}>No numeric columns scaled.</span>}
      </Section>

      {/* Feature selection */}
      <Section title="Feature Selection Report">
        {Object.keys(featureDropped).some((k) => (featureDropped[k] || []).length > 0) ? (
          <>
            {featureDropped.correlation?.length > 0 && (
              <div style={{ marginBottom: "6px" }}>
                <strong style={{ fontSize: "12px" }}>Dropped (high correlation):</strong>{" "}
                <span style={{ color: "#dc2626", fontSize: "12px" }}>{featureDropped.correlation.join(", ")}</span>
              </div>
            )}
            {featureDropped.mutual_info?.length > 0 && (
              <div style={{ marginBottom: "6px" }}>
                <strong style={{ fontSize: "12px" }}>Dropped (low mutual info):</strong>{" "}
                <span style={{ color: "#d97706", fontSize: "12px" }}>{featureDropped.mutual_info.join(", ")}</span>
              </div>
            )}
            {featureDropped.low_importance?.length > 0 && (
              <div style={{ marginBottom: "6px" }}>
                <strong style={{ fontSize: "12px" }}>Dropped (low ExtraTrees importance):</strong>{" "}
                <span style={{ color: "#7c3aed", fontSize: "12px" }}>{featureDropped.low_importance.join(", ")}</span>
              </div>
            )}
          </>
        ) : <span style={{ color: "#16a34a", fontSize: "13px" }}>All features passed selection criteria.</span>}

        {Object.keys(featureImportances).length > 0 && (
          <div style={{ marginTop: "10px" }}>
            <strong style={{ fontSize: "12px", display: "block", marginBottom: "6px" }}>Top Feature Importances</strong>
            {Object.entries(featureImportances)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 10)
              .map(([col, score]) => (
                <div key={col} style={{ marginBottom: "4px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "2px" }}>
                    <span>{col}</span><span style={{ color: "#6b7280" }}>{(score * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ background: "#e2e8f0", borderRadius: "4px", height: "6px" }}>
                    <div style={{ width: `${Math.min(100, score * 100)}%`, background: "#3b82f6", height: "6px", borderRadius: "4px" }} />
                  </div>
                </div>
              ))}
          </div>
        )}
      </Section>

      {/* Discretization */}
      {Object.keys(discReport).length > 0 && (
        <Section title="Discretization (Binning)">
          <KVTable
            data={Object.fromEntries(Object.entries(discReport).map(([k, v]) => [k, `${v.method} → ${v.result_column} (${v.n_bins} bins)`]))}
            keyLabel="Column" valLabel="Applied"
          />
        </Section>
      )}

      {/* Dim reduction */}
      {!dimReport?.skipped && dimReport?.method && (
        <Section title="Dimensionality Reduction">
          <Badge label="Method" value={dimReport.method?.toUpperCase()} bg="#f3e8ff" color="#7c3aed" />
          {dimReport.components_kept && <Badge label="Components kept" value={dimReport.components_kept} />}
          {dimReport.variance_explained && <Badge label="Variance explained" value={`${(dimReport.variance_explained * 100).toFixed(1)}%`} />}
        </Section>
      )}

      {/* Dropped columns */}
      <Section title="Dropped Columns">
        {cleanedResult.dropped_columns?.length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {cleanedResult.dropped_columns.map((c) => (
              <span key={c} style={{ fontSize: "12px", padding: "3px 9px", borderRadius: "99px", background: "#fee2e2", color: "#dc2626", fontWeight: 500 }}>{c}</span>
            ))}
          </div>
        ) : <span style={{ color: "#16a34a", fontSize: "13px" }}>No columns dropped.</span>}
      </Section>

      {/* Dataset preview */}
      <Section title={`Cleaned Dataset Preview (top 30 rows) — ${headers.length} columns`}>
        {previewRows.length ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", minWidth: "760px", fontSize: "12px" }}>
              <thead>
                <tr>
                  {headers.map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e2e8f0", background: "#f8fafc", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    {headers.map((h) => (
                      <td key={`${i}-${h}`} style={{ padding: "6px 10px", whiteSpace: "nowrap" }}>{String(row[h] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p>No preview rows available.</p>}
      </Section>

      </>
    </section>
  );
}
