export default function FeatureSelectionView({ report }) {
	if (!report) {
		return null;
	}

	const removed = report.results?.removed_features || [];
	const finalShape = report.results?.final_shape || [];

	return (
		<div style={{ marginTop: "16px", padding: "12px", border: "1px solid #e2e8f0" }}>
			<h3>Feature Engineering Summary</h3>
			<p>Final Shape: {finalShape.join(" x ") || "N/A"}</p>
			<p>Removed Features: {removed.length ? removed.join(", ") : "None"}</p>
		</div>
	);
}
