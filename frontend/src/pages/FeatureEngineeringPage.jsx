import { useState } from "react";

function Toggle({ label, hint, checked, onChange }) {
  return (
    <label style={{ display: "flex", alignItems: "flex-start", gap: "10px", marginBottom: "12px", cursor: "pointer" }}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ marginTop: "2px", width: "16px", height: "16px" }}
      />
      <div>
        <div style={{ fontWeight: 600, fontSize: "14px" }}>{label}</div>
        {hint && <div style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>{hint}</div>}
      </div>
    </label>
  );
}

export default function FeatureEngineeringPage({ onRunCleaning, loading }) {
  const [enableFeatureEngineering, setEnableFeatureEngineering] = useState(true);
  const [enableDiscretization, setEnableDiscretization] = useState(false);
  const [enableDimReduction, setEnableDimReduction] = useState(false);
  const [dimReductionMethod, setDimReductionMethod] = useState("");
  const [domain, setDomain] = useState("general");
  const [enableOptimizer, setEnableOptimizer] = useState(true);
  const [enableHistory, setEnableHistory] = useState(true);
  const [enableFeatureSuggestions, setEnableFeatureSuggestions] = useState(true);

  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px", marginTop: "14px" }}>
      <h2 style={{ marginTop: 0 }}>Step 5: Advanced Pipeline Options</h2>
      <p style={{ color: "#64748b", marginBottom: "14px" }}>Configure optional preprocessing steps before running the full AI pipeline.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: "16px", marginBottom: "16px" }}>

        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px" }}>
          <div style={{ fontWeight: 700, marginBottom: "10px", color: "#374151" }}>Domain Selection</div>
          <label style={{ fontSize: "12px", color: "#475569", display: "block", marginBottom: "4px" }}>Dataset domain:</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{ padding: "6px 10px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px", width: "100%" }}
          >
            <option value="general">General</option>
            <option value="finance">Finance</option>
            <option value="healthcare">Healthcare</option>
            <option value="sales">Sales</option>
            <option value="iot">IoT</option>
          </select>
        </div>

        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px" }}>
          <div style={{ fontWeight: 700, marginBottom: "10px", color: "#374151" }}>Feature Engineering</div>
          <Toggle
            label="Enable derived features"
            hint="Extract date parts (year/month/day) and numeric ratio features"
            checked={enableFeatureEngineering}
            onChange={setEnableFeatureEngineering}
          />
        </div>

        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px" }}>
          <div style={{ fontWeight: 700, marginBottom: "10px", color: "#374151" }}>Discretization (Binning)</div>
          <Toggle
            label="Enable auto-discretization"
            hint="Bin high-skew or wide-range numerics (equal-width, equal-freq, KMeans)"
            checked={enableDiscretization}
            onChange={setEnableDiscretization}
          />
        </div>

        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px" }}>
          <div style={{ fontWeight: 700, marginBottom: "10px", color: "#374151" }}>Dimensionality Reduction</div>
          <Toggle
            label="Enable dimensionality reduction"
            hint="PCA (regression, >20 features) or LDA (classification, >15 features)"
            checked={enableDimReduction}
            onChange={setEnableDimReduction}
          />
          {enableDimReduction && (
            <div style={{ marginTop: "8px" }}>
              <label style={{ fontSize: "12px", color: "#475569", display: "block", marginBottom: "4px" }}>Force method (auto if blank):</label>
              <select
                value={dimReductionMethod}
                onChange={(e) => setDimReductionMethod(e.target.value)}
                style={{ padding: "6px 10px", border: "1px solid #cbd5e1", borderRadius: "6px", fontSize: "13px", width: "100%" }}
              >
                <option value="">Auto (AI decides)</option>
                <option value="pca">PCA</option>
                <option value="lda">LDA</option>
                <option value="none">None (skip)</option>
              </select>
            </div>
          )}
        </div>

        <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px" }}>
          <div style={{ fontWeight: 700, marginBottom: "10px", color: "#374151" }}>Advanced AI Modules</div>
          <Toggle
            label="Enable pipeline optimizer"
            hint="Tests Standard, Robust, and MinMax variants with simple ML models"
            checked={enableOptimizer}
            onChange={setEnableOptimizer}
          />
          <Toggle
            label="Enable history learning"
            hint="Uses previous runs to suggest preprocessing choices"
            checked={enableHistory}
            onChange={setEnableHistory}
          />
          <Toggle
            label="Enable feature suggestions"
            hint="Suggests ratio/difference/interaction/date-part features"
            checked={enableFeatureSuggestions}
            onChange={setEnableFeatureSuggestions}
          />
        </div>
      </div>

      <button
        type="button"
        disabled={loading}
        onClick={() => onRunCleaning({
          enableFeatureEngineering,
          enableDiscretization,
          enableDimReduction,
          dimReductionMethod: enableDimReduction ? dimReductionMethod : null,
          domain,
          enableOptimizer,
          enableHistory,
          enableFeatureSuggestions,
        })}
        style={{
          padding: "11px 20px",
          border: "none",
          borderRadius: "8px",
          background: loading ? "#94a3b8" : "linear-gradient(90deg, #16a34a, #059669)",
          color: "white",
          fontWeight: 700,
          fontSize: "14px",
          cursor: loading ? "not-allowed" : "pointer",
          transition: "opacity 0.2s",
        }}
      >
        {loading ? "Running AI Pipeline..." : "Run Automated Cleaning Pipeline"}
      </button>
    </section>
  );
}
