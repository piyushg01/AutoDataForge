export default function Dashboard() {
	return (
		<section style={{ display: "grid", gap: "14px" }}>
			<div style={{ padding: "20px", borderRadius: "14px", border: "1px solid #bfdbfe", background: "linear-gradient(135deg, #eff6ff, #ffffff)" }}>
				<h2 style={{ marginTop: 0, marginBottom: "8px" }}>Phase 1: Autonomous Data Preparation</h2>
				<p style={{ margin: 0, color: "#334155" }}>
					Upload CSV/Excel, select target column, and instantly get fully cleaned
					<code style={{ marginLeft: "6px", marginRight: "6px" }}>cleaned_dataset.csv</code>
					ready for model training in next phase.
				</p>
			</div>

			<div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
				<div style={{ padding: "14px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#fff" }}>
					<strong>Cleaning</strong>
					<p style={{ marginBottom: 0, color: "#475569" }}>Missing values, duplicates, outliers handled automatically.</p>
				</div>
				<div style={{ padding: "14px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#fff" }}>
					<strong>Preprocessing</strong>
					<p style={{ marginBottom: 0, color: "#475569" }}>Encoding + scaling applied to relevant feature columns.</p>
				</div>
				<div style={{ padding: "14px", border: "1px solid #e2e8f0", borderRadius: "12px", background: "#fff" }}>
					<strong>Output</strong>
					<p style={{ marginBottom: 0, color: "#475569" }}>Download updated cleaned file directly from Upload page.</p>
				</div>
			</div>
		</section>
	);
}
