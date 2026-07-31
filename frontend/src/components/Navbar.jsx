export default function Navbar() {
	return (
		<nav
			style={{
				padding: "14px 20px",
				borderBottom: "1px solid #dbeafe",
				marginBottom: "16px",
				background: "#ffffffd9",
				position: "sticky",
				top: 0,
				backdropFilter: "blur(8px)",
				zIndex: 10,
			}}
		>
			<div>
				<strong style={{ marginRight: "18px", fontSize: "20px", color: "#1e3a8a" }}>Autonomous Data Preparation System</strong>
				<div style={{ color: "#475569", marginTop: "4px" }}>Phase-1: EDA, Column Analysis, Cleaning & Preprocessing</div>
			</div>
		</nav>
	);
}
