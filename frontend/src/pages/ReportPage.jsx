export default function ReportPage({ result }) {
	return (
		<section style={{ background: "#ffffff", borderRadius: "14px", padding: "18px", border: "1px solid #e2e8f0" }}>
			<h2 style={{ marginTop: 0 }}>Phase 1 Report</h2>
			{!result ? <p>No report available yet. Process a dataset from Upload page.</p> : null}
			{result ? (
				<>
					<p><strong>Target:</strong> {result.target_column}</p>
					<p><strong>Rows:</strong> {result.rows} | <strong>Columns:</strong> {result.columns}</p>
					<p><strong>Scaler:</strong> {result.scaler}</p>
					<p><strong>Dropped Columns:</strong> {(result.dropped_columns || []).length ? result.dropped_columns.join(", ") : "None"}</p>
					<p><strong>Selected Features:</strong> {(result.selected_features || []).length ? result.selected_features.join(", ") : "None"}</p>
				</>
			) : null}
		</section>
	);
}
