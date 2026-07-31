import { useState } from "react";

export default function FileUpload({ onSubmit, loading }) {
	const [file, setFile] = useState(null);
	const [targetColumnName, setTargetColumnName] = useState("");

	const handleSubmit = (event) => {
		event.preventDefault();
		if (!file || !targetColumnName.trim() || loading) {
			return;
		}
		onSubmit(file, targetColumnName.trim());
	};

	return (
		<form
			onSubmit={handleSubmit}
			style={{
				display: "grid",
				gap: "12px",
				maxWidth: "620px",
				padding: "16px",
				border: "1px solid #dbeafe",
				borderRadius: "12px",
				background: "#f8fbff",
			}}
		>
			<input
				type="file"
				accept=".csv,.xlsx,.xls"
				onChange={(event) => setFile(event.target.files?.[0] || null)}
				style={{ padding: "8px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
			/>
			<input
				type="text"
				placeholder="Target column name (required)"
				value={targetColumnName}
				onChange={(event) => setTargetColumnName(event.target.value)}
				style={{ padding: "10px", border: "1px solid #cbd5e1", borderRadius: "8px" }}
			/>
			<button
				type="submit"
				disabled={!file || !targetColumnName.trim() || loading}
				style={{
					padding: "10px 14px",
					border: "none",
					borderRadius: "8px",
					background: "linear-gradient(90deg, #2563eb, #0ea5e9)",
					color: "white",
					fontWeight: 600,
					cursor: "pointer",
				}}
			>
				{loading ? "Processing..." : "Upload & Clean Dataset"}
			</button>
		</form>
	);
}
