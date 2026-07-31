import { getDownloadUrl } from "../services/api";

export default function DataPreview({ result }) {
	if (!result) {
		return null;
	}

	const downloadUrls = result.download_urls || {};

	return (
		<div style={{ marginTop: "16px", padding: "14px", border: "1px solid #bfdbfe", borderRadius: "12px", background: "#f8fbff" }}>
			<h3 style={{ marginTop: 0 }}>Updated File Ready</h3>
			<p style={{ marginBottom: "6px" }}>Target Column Preserved: <strong>{result.target_column}</strong></p>
			<p style={{ marginBottom: "6px" }}>Rows: <strong>{result.rows}</strong> | Columns: <strong>{result.columns}</strong></p>
			<p style={{ marginBottom: "6px" }}>Saved As: <strong>cleaned_dataset.csv</strong></p>
			<p style={{ marginBottom: "6px" }}>Path: {result.cleaned_dataset_path}</p>

			<div style={{ marginTop: "12px", display: "grid", gap: "8px", maxWidth: "520px" }}>
				<strong>Download</strong>
				{downloadUrls.cleaned ? (
					<a
						href={getDownloadUrl(downloadUrls.cleaned)}
						target="_blank"
						rel="noreferrer"
						style={{ color: "#1d4ed8", fontWeight: 600 }}
					>
						Download cleaned_dataset.csv
					</a>
				) : null}
			</div>
		</div>
	);
}
