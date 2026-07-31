import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { useState } from "react";
import { Bar, Scatter } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, Tooltip, Legend);

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
];

function StatCard({ label, value, color = "#dbeafe" }) {
  return (
    <div style={{ padding: "12px 16px", border: "1px solid #e2e8f0", borderRadius: "10px", background: color }}>
      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: "22px", fontWeight: 700, color: "#1e293b", marginTop: "4px" }}>{value}</div>
    </div>
  );
}

function BoxplotCard({ box }) {
  const range = box.max - box.min || 1;
  const pct = (v) => Math.max(0, Math.min(100, ((v - box.min) / range) * 100));
  return (
    <div style={{ border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px", background: "#f8fafc", marginBottom: "8px" }}>
      <div style={{ fontWeight: 600, fontSize: "13px", marginBottom: "6px", color: "#374151" }}>{box.column}</div>
      <div style={{ position: "relative", height: "28px", background: "#e2e8f0", borderRadius: "4px", overflow: "hidden" }}>
        {/* IQR box */}
        <div style={{
          position: "absolute",
          left: `${pct(box.q1)}%`,
          width: `${pct(box.q3) - pct(box.q1)}%`,
          top: "4px", height: "20px",
          background: "#3b82f6", borderRadius: "3px",
        }} />
        {/* Median line */}
        <div style={{
          position: "absolute",
          left: `${pct(box.median)}%`,
          width: "2px", top: "2px", height: "24px",
          background: "#1d4ed8",
        }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
        <span>Min: {box.min?.toFixed(2)}</span>
        <span>Q1: {box.q1?.toFixed(2)}</span>
        <span>Median: {box.median?.toFixed(2)}</span>
        <span>Q3: {box.q3?.toFixed(2)}</span>
        <span>Max: {box.max?.toFixed(2)}</span>
      </div>
      <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
        Mean: {box.mean?.toFixed(3)} | Std: {box.std?.toFixed(3)}
      </div>
    </div>
  );
}

export default function DatasetDashboard({ profileData }) {
  const [activeHistIdx, setActiveHistIdx] = useState(0);
  const [activeCatIdx, setActiveCatIdx] = useState(0);

  if (!profileData) {
    return (
      <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px" }}>
        <h2 style={{ marginTop: 0 }}>Step 2: Dataset Dashboard</h2>
        <p style={{ color: "#64748b" }}>Upload a dataset to see EDA summary and visualizations.</p>
      </section>
    );
  }

  const { profile, charts } = profileData;
  const histograms = charts?.numeric_histograms || [];
  const boxplots = charts?.numeric_boxplots || [];
  const categoryBars = charts?.categorical_bars || [];
  const corr = charts?.correlation_heatmap;
  const skewness = charts?.skewness || {};

  const currentHist = histograms[activeHistIdx];
  const currentCat = categoryBars[activeCatIdx];

  const histChartData = currentHist
    ? {
        labels: currentHist.values.map((_, i) => String(i + 1)),
        datasets: [{
          label: currentHist.column,
          data: currentHist.values,
          backgroundColor: "#3b82f680",
          borderColor: "#3b82f6",
          borderWidth: 1,
        }],
      }
    : null;

  const catChartData = currentCat
    ? {
        labels: currentCat.labels,
        datasets: [{
          label: currentCat.column,
          data: currentCat.values,
          backgroundColor: currentCat.labels.map((_, i) => COLORS[i % COLORS.length] + "99"),
          borderColor: currentCat.labels.map((_, i) => COLORS[i % COLORS.length]),
          borderWidth: 1,
        }],
      }
    : null;

  const corrPoints = [];
  if (corr?.matrix?.length) {
    for (let i = 0; i < corr.matrix.length; i++) {
      for (let j = 0; j < corr.matrix[i].length; j++) {
        const v = corr.matrix[i][j];
        corrPoints.push({ x: i, y: j, v });
      }
    }
  }

  const missingCols = profile.column_summary.filter((r) => r.missing_pct > 0);

  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
      <h2 style={{ marginTop: 0 }}>Step 2: Dataset Dashboard</h2>

      {/* Stats bar */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: "10px", marginBottom: "18px" }}>
        <StatCard label="Total Rows" value={profile.rows} />
        <StatCard label="Total Columns" value={profile.columns} />
        <StatCard label="Numeric" value={profile.schema.numeric.length} color="#f0fdf4" />
        <StatCard label="Categorical" value={profile.schema.categorical.length} color="#fef9c3" />
        <StatCard label="Text / Other" value={profile.schema.text.length} color="#fdf4ff" />
        <StatCard label="Datetime" value={profile.schema.datetime.length} color="#fff7ed" />
        <StatCard label="Missing Cols" value={missingCols.length} color={missingCols.length > 0 ? "#fef2f2" : "#f0fdf4"} />
      </div>

      {/* Column summary table */}
      <h3 style={{ marginBottom: "8px" }}>Column Summary</h3>
      <div style={{ overflowX: "auto", marginBottom: "20px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["Column", "Type", "Missing %", "Unique", "Skewness"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "8px 10px", borderBottom: "1px solid #e2e8f0", color: "#475569" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {profile.column_summary.map((row) => (
              <tr key={row.column} style={{ borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "7px 10px", fontWeight: 500 }}>{row.column}</td>
                <td style={{ padding: "7px 10px" }}>
                  <span style={{
                    fontSize: "11px", padding: "2px 8px", borderRadius: "999px", fontWeight: 600,
                    background: row.detected_type === "numeric" ? "#dbeafe" : row.detected_type === "categorical" ? "#fef9c3" : "#f3f4f6",
                    color: row.detected_type === "numeric" ? "#1d4ed8" : row.detected_type === "categorical" ? "#92400e" : "#374151",
                  }}>{row.detected_type}</span>
                </td>
                <td style={{ padding: "7px 10px", color: row.missing_pct > 20 ? "#dc2626" : row.missing_pct > 5 ? "#d97706" : "#16a34a" }}>
                  {row.missing_pct}%
                </td>
                <td style={{ padding: "7px 10px" }}>{row.unique_values}</td>
                <td style={{ padding: "7px 10px", color: "#6b7280" }}>
                  {skewness[row.column] != null ? skewness[row.column].toFixed(2) : "–"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: "16px" }}>

        {/* Histogram panel */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <h4 style={{ margin: 0, fontSize: "13px" }}>Distribution</h4>
            <select
              value={activeHistIdx}
              onChange={(e) => setActiveHistIdx(Number(e.target.value))}
              style={{ fontSize: "12px", padding: "2px 6px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
            >
              {histograms.map((h, i) => (
                <option key={h.column} value={i}>{h.column}</option>
              ))}
            </select>
          </div>
          {histChartData
            ? <Bar data={histChartData} options={{ plugins: { legend: { display: false } }, scales: { x: { ticks: { maxTicksLimit: 8 } } } }} />
            : <p style={{ color: "#94a3b8" }}>No numeric columns</p>}
        </div>

        {/* Category bar panel */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <h4 style={{ margin: 0, fontSize: "13px" }}>Categorical Frequency</h4>
            <select
              value={activeCatIdx}
              onChange={(e) => setActiveCatIdx(Number(e.target.value))}
              style={{ fontSize: "12px", padding: "2px 6px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
            >
              {categoryBars.map((c, i) => (
                <option key={c.column} value={i}>{c.column}</option>
              ))}
            </select>
          </div>
          {catChartData
            ? <Bar data={catChartData} options={{ indexAxis: "y", plugins: { legend: { display: false } } }} />
            : <p style={{ color: "#94a3b8" }}>No categorical columns</p>}
        </div>

        {/* Correlation heatmap */}
        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px" }}>
          <h4 style={{ margin: "0 0 8px 0", fontSize: "13px" }}>Correlation Heatmap</h4>
          {corrPoints.length ? (
            <Scatter
              data={{
                datasets: [{
                  label: "r",
                  data: corrPoints,
                  pointRadius: corrPoints.length < 100 ? 8 : 5,
                  pointBackgroundColor: corrPoints.map(({ v }) => {
                    const abs = Math.abs(v);
                    if (abs > 0.7) return v > 0 ? "#1d4ed8" : "#dc2626";
                    if (abs > 0.4) return v > 0 ? "#60a5fa" : "#f87171";
                    return "#cbd5e1";
                  }),
                }],
              }}
              options={{
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ({ raw }) => `r=${raw.v.toFixed(2)}` } } },
                scales: {
                  x: { ticks: { callback: (v) => (corr.columns[v] || "").slice(0, 8) } },
                  y: { ticks: { callback: (v) => (corr.columns[v] || "").slice(0, 8) } },
                },
              }}
            />
          ) : <p style={{ color: "#94a3b8" }}>Not enough numeric columns</p>}
        </div>
      </div>

      {/* Boxplots */}
      {boxplots.length > 0 && (
        <>
          <h3 style={{ margin: "20px 0 10px" }}>Numeric Boxplot Statistics</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: "10px" }}>
            {boxplots.map((box) => <BoxplotCard key={box.column} box={box} />)}
          </div>
        </>
      )}

      {/* Missing values summary */}
      {missingCols.length > 0 && (
        <div style={{ marginTop: "18px", border: "1px solid #fecaca", borderRadius: "10px", padding: "12px", background: "#fff5f5" }}>
          <h4 style={{ margin: "0 0 8px 0", color: "#dc2626" }}>Columns with Missing Values</h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {missingCols.map((c) => (
              <span key={c.column} style={{
                padding: "3px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 600,
                background: c.missing_pct > 40 ? "#fee2e2" : c.missing_pct > 20 ? "#fef3c7" : "#f1f5f9",
                color: c.missing_pct > 40 ? "#dc2626" : c.missing_pct > 20 ? "#92400e" : "#475569",
              }}>
                {c.column} ({c.missing_pct}%)
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
