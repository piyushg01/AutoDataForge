import { useState } from "react";

import { profileDataset } from "../services/api";

export default function UploadPage({ onProfileReady }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file || loading) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      const profile = await profileDataset(file);
      onProfileReady({ file, profile });
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || "Upload failed";
      setError(String(detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "14px", padding: "18px" }}>
      <h2 style={{ marginTop: 0 }}>Step 1: Upload Dataset</h2>
      <p style={{ color: "#475569" }}>Upload a CSV or Excel file to start automated Phase-1 data analysis and cleaning.</p>
      <form onSubmit={handleUpload} style={{ display: "grid", gap: "12px", maxWidth: "640px" }}>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
        />
        <button
          type="submit"
          disabled={!file || loading}
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
          {loading ? "Profiling Dataset..." : "Upload & Profile"}
        </button>
      </form>
      {error ? <p style={{ marginTop: "10px", color: "#dc2626" }}>{error}</p> : null}
    </section>
  );
}
