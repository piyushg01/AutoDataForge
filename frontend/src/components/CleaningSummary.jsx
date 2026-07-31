export default function CleaningSummary({ result }) {
	if (!result) {
		return null;
	}

	return (
		<div style={{ marginTop: "16px", padding: "14px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#ffffff" }}>
			<h3 style={{ marginTop: 0 }}>Cleaning Summary</h3>
			<p>Duplicates Removed: <strong>{result.duplicates_removed ?? 0}</strong></p>
			<p>Outliers Capped (IQR): <strong>{result.outliers_capped ?? 0}</strong></p>
			<p>Scaler Used: <strong>{result.scaler || "none"}</strong></p>
			<p>Encoded Features: <strong>{result.encoded_feature_count ?? 0}</strong></p>
			<p>
				Dropped Columns: <strong>{(result.dropped_columns || []).length ? result.dropped_columns.join(", ") : "None"}</strong>
			</p>
		</div>
	);
}
