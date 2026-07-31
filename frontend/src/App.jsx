import { useMemo, useState } from "react";

import CleaningSuggestionPage from "./pages/CleaningSuggestionPage";
import CleanedDatasetPreview from "./pages/CleanedDatasetPreview";
import DatasetDashboard from "./pages/DatasetDashboard";
import AuditView from "./pages/AuditView";
import FeatureEngineeringPage from "./pages/FeatureEngineeringPage";
import HistoryView from "./pages/HistoryView";
import OptimizerView from "./pages/OptimizerView";
import ReportView from "./pages/ReportView";
import SimilarityView from "./pages/SimilarityView";
import TargetSelectionPage from "./pages/TargetSelectionPage";
import UploadPage from "./pages/UploadPage";
import VersionsView from "./pages/VersionsView";
import { analyzeDatasetColumns, runPhase1Cleaning } from "./services/api";
import "./App.css";

const NAV_ITEMS = [
  "Overview",
  "Visualizations",
  "Column Analysis",
  "Pipeline",
  "Optimizer",
  "History",
  "Similarity",
  "Versions",
  "Audit Log",
  "Final Report",
  "Cleaned Data",
];

function ShellCard({ title, children }) {
  return (
    <section className="shell-card">
      <h3 style={{ margin: "0 0 10px 0", color: "#0f172a", fontSize: "14px", letterSpacing: "0.01em" }}>{title}</h3>
      {children}
    </section>
  );
}

function MetricCard({ label, value, accent = "#2563eb" }) {
  return (
    <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px" }}>
      <div style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ marginTop: "6px", color: accent, fontSize: "20px", fontWeight: 700 }}>{value}</div>
    </div>
  );
}

export default function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [profilePayload, setProfilePayload] = useState(null);
  const [targetConfig, setTargetConfig] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedDrops, setSelectedDrops] = useState([]);
  const [cleanedResult, setCleanedResult] = useState(null);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingClean, setLoadingClean] = useState(false);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const columns = useMemo(() => profilePayload?.columns || [], [profilePayload]);
  const optimizerResult = cleanedResult?.optimizer_result || cleanedResult?.optimization || {};
  const backendFiles = cleanedResult?.backend_files || {};
  const auditRows = cleanedResult?.audit_log || backendFiles?.audit_log || [];
  const historyRows = backendFiles?.pipeline_history || [];
  const similarityRows =
    cleanedResult?.similarity?.match?.top_matches ||
    cleanedResult?.similarity?.pipeline?.top_matches ||
    [];
  const finalReport = cleanedResult?.final_report || backendFiles?.final_report || {};

  const handleProfileReady = ({ file, profile }) => {
    setUploadedFile(file);
    setProfilePayload(profile);
    setTargetConfig(null);
    setSuggestions([]);
    setSelectedDrops([]);
    setCleanedResult(null);
    setError("");
  };

  const handleTargetSelect = async ({ targetColumn, problemType }) => {
    if (!uploadedFile) {
      return;
    }

    try {
      setLoadingAnalyze(true);
      setError("");
      const analyzed = await analyzeDatasetColumns(uploadedFile, targetColumn);
      setTargetConfig({ targetColumn, problemType });
      setSuggestions(analyzed.processing_suggestions || []);
      setSelectedDrops(
        (analyzed.processing_suggestions || [])
          .filter((row) => String(row.action || "").toLowerCase().includes("remove"))
          .map((row) => row.column)
      );
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || "Column analysis failed";
      setError(String(detail));
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const handleToggleDrop = (column) => {
    setSelectedDrops((prev) =>
      prev.includes(column) ? prev.filter((item) => item !== column) : [...prev, column]
    );
  };

  const handleRunCleaning = async ({
    enableFeatureEngineering,
    enableDiscretization,
    enableDimReduction,
    dimReductionMethod,
    domain,
    enableOptimizer,
    enableHistory,
    enableFeatureSuggestions,
  }) => {
    if (!uploadedFile || !targetConfig) {
      return;
    }

    try {
      setLoadingClean(true);
      setError("");
      const cleaned = await runPhase1Cleaning({
        file: uploadedFile,
        targetColumnName: targetConfig.targetColumn,
        problemType: targetConfig.problemType,
        confirmedDropColumns: selectedDrops,
        enableFeatureEngineering,
        enableDiscretization,
        enableDimReduction,
        dimReductionMethod,
        domain,
        enableOptimizer,
        enableHistory,
        enableFeatureSuggestions,
      });
      setCleanedResult(cleaned);
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || "Cleaning failed";
      setError(String(detail));
    } finally {
      setLoadingClean(false);
    }
  };

  return (
    <div className="app-shell">
      <aside className={`side-nav ${sidebarOpen ? "open" : ""}`}>
        <div style={{ padding: "8px 10px", marginBottom: "10px" }}>
          <div style={{ fontSize: "13px", color: "#93c5fd", textTransform: "uppercase", letterSpacing: "0.08em" }}>AI Data Platform</div>
          <div style={{ fontSize: "16px", fontWeight: 700, marginTop: "4px", color: "#f8fafc" }}>Autonomous Prep Studio</div>
        </div>
        <nav style={{ display: "grid", gap: "5px" }}>
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setActivePage(item);
                setSidebarOpen(false);
              }}
              className={`side-nav-item ${activePage === item ? "active" : ""}`}
            >
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <div className="main-shell">
        <header className="top-status-bar">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button className="menu-toggle" type="button" onClick={() => setSidebarOpen((prev) => !prev)}>
              ☰
            </button>
            <div style={{ color: "#0f172a", fontWeight: 800, fontSize: "18px" }}>{activePage}</div>
          </div>
          <div className="status-pill-row">
            <span className={`status-pill ${uploadedFile ? "success" : "muted"}`}>Upload {uploadedFile ? "Ready" : "Pending"}</span>
            <span className={`status-pill ${targetConfig ? "info" : "muted"}`}>Target {targetConfig ? "Set" : "Pending"}</span>
            <span className={`status-pill ${cleanedResult ? "warn" : "muted"}`}>Pipeline {cleanedResult ? "Complete" : "Idle"}</span>
          </div>
        </header>

        <main className="content-area">
          {activePage === "Overview" && (
            <>
              <ShellCard title="Project Overview">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: "10px" }}>
                  <MetricCard label="Rows" value={cleanedResult?.rows ?? profilePayload?.profile?.rows ?? 0} />
                  <MetricCard label="Columns" value={cleanedResult?.columns ?? profilePayload?.profile?.columns ?? 0} />
                  <MetricCard label="Best Pipeline" value={cleanedResult?.best_pipeline || "-"} accent="#7c3aed" />
                  <MetricCard label="Best Score" value={cleanedResult?.score ?? "-"} accent="#0f766e" />
                  <MetricCard label="Risk" value={finalReport?.risk_level || "-"} accent="#dc2626" />
                  <MetricCard label="Quality" value={finalReport?.dataset_quality_score ?? "-"} accent="#2563eb" />
                </div>
              </ShellCard>
              <div className="panel-wrap"><UploadPage onProfileReady={handleProfileReady} /></div>
              {error ? <p style={{ color: "#dc2626", fontWeight: 600 }}>{error}</p> : null}
            </>
          )}

          {activePage === "Visualizations" && <div className="panel-wrap"><DatasetDashboard profileData={profilePayload} /></div>}

          {activePage === "Column Analysis" && (
            <>
              <div className="panel-wrap"><TargetSelectionPage columns={columns} onSelectTarget={handleTargetSelect} /></div>
              {loadingAnalyze ? <p>Analyzing columns...</p> : null}
              <div className="panel-wrap"><CleaningSuggestionPage
                suggestions={suggestions}
                selectedDrops={selectedDrops}
                onToggleDrop={handleToggleDrop}
              /></div>
              {error ? <p style={{ color: "#dc2626", fontWeight: 600 }}>{error}</p> : null}
            </>
          )}

          {activePage === "Pipeline" && (
            <>
              <div className="panel-wrap"><FeatureEngineeringPage onRunCleaning={handleRunCleaning} loading={loadingClean} /></div>
              {cleanedResult ? (
                <ShellCard title="Pipeline Summary">
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: "10px" }}>
                    <MetricCard label="Duplicates Removed" value={cleanedResult.duplicates_removed ?? 0} />
                    <MetricCard label="Outliers Capped" value={cleanedResult.outliers_capped ?? 0} />
                    <MetricCard label="Chosen Scaler" value={cleanedResult.chosen_scaler || cleanedResult.scaler || "-"} accent="#92400e" />
                    <MetricCard label="Chosen Encoding" value={cleanedResult.chosen_encoding || "-"} accent="#1d4ed8" />
                  </div>
                </ShellCard>
              ) : null}
              {error ? <p style={{ color: "#dc2626", fontWeight: 600 }}>{error}</p> : null}
            </>
          )}

          {activePage === "Optimizer" && (
            <ShellCard title="Optimizer">
              <OptimizerView optimization={optimizerResult} />
            </ShellCard>
          )}

          {activePage === "History" && (
            <ShellCard title="Pipeline History">
              <HistoryView history={historyRows} />
            </ShellCard>
          )}

          {activePage === "Similarity" && (
            <ShellCard title="Similarity Matches">
              <SimilarityView similarity={similarityRows} />
            </ShellCard>
          )}

          {activePage === "Versions" && (
            <ShellCard title="Version Files">
              <VersionsView versions={cleanedResult?.versions} />
            </ShellCard>
          )}

          {activePage === "Audit Log" && (
            <ShellCard title="Audit Log">
              <AuditView audit={auditRows} />
            </ShellCard>
          )}

          {activePage === "Final Report" && (
            <ShellCard title="Final Report">
              <ReportView report={finalReport} />
            </ShellCard>
          )}

          {activePage === "Cleaned Data" && <div className="panel-wrap"><CleanedDatasetPreview cleanedResult={cleanedResult} /></div>}
        </main>
      </div>
      {sidebarOpen ? <button type="button" className="nav-overlay" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar" /> : null}
    </div>
  );
}
