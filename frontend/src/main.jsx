import React, { useEffect } from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

const showBootError = (message) => {
	const fallback = document.getElementById("boot-fallback");
	if (fallback) {
		fallback.innerHTML = `
			<h1>Autonomous Data Prep Dashboard</h1>
			<p style="color:#b91c1c">${message}</p>
		`;
	}
};

window.addEventListener("error", (event) => {
	showBootError(`Startup error: ${event.message}`);
});

window.addEventListener("unhandledrejection", (event) => {
	const reason = event.reason?.message || String(event.reason || "Unknown promise rejection");
	showBootError(`Startup error: ${reason}`);
});

function BootReady({ children }) {
	useEffect(() => {
		const fallback = document.getElementById("boot-fallback");
		if (fallback) {
			fallback.style.display = "none";
		}
	}, []);

	return children;
}

class AppErrorBoundary extends React.Component {
	constructor(props) {
		super(props);
		this.state = { hasError: false, message: "" };
	}

	static getDerivedStateFromError(error) {
		return { hasError: true, message: error?.message || "Unknown render error" };
	}

	componentDidCatch(error) {
		showBootError(`Startup error: ${error?.message || "Unknown render error"}`);
	}

	render() {
		if (this.state.hasError) {
			return (
				<div style={{ padding: "24px", color: "#b91c1c", fontFamily: "Arial, sans-serif" }}>
					<h1>Autonomous Data Prep Dashboard</h1>
					<p>Startup error: {this.state.message}</p>
				</div>
			);
		}

		return this.props.children;
	}
}

try {
	const rootElement = document.getElementById("root");
	if (!rootElement) {
		throw new Error("Root element not found");
	}

	ReactDOM.createRoot(rootElement).render(
		<React.StrictMode>
			<AppErrorBoundary>
				<BootReady>
					<App />
				</BootReady>
			</AppErrorBoundary>
		</React.StrictMode>
	);
} catch (error) {
	showBootError(`Startup error: ${error.message}`);
}
