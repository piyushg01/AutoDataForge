import axios from "axios";

export const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
	baseURL: `${API_BASE_URL}/api`,
	timeout: 120000,
});

export const profileDataset = async (file) => {
	const form = new FormData();
	form.append("file", file);

	const { data } = await api.post("/profile", form, {
		headers: { "Content-Type": "multipart/form-data" },
	});
	return data;
};

export const analyzeDatasetColumns = async (file, targetColumnName) => {
	const form = new FormData();
	form.append("file", file);
	form.append("target_column_name", targetColumnName);

	const { data } = await api.post("/analyze", form, {
		headers: { "Content-Type": "multipart/form-data" },
	});
	return data;
};

export const runPhase1Cleaning = async ({
	file,
	targetColumnName,
	problemType,
	confirmedDropColumns = [],
	enableFeatureEngineering = true,
	enableDiscretization = false,
	enableDimReduction = false,
	dimReductionMethod = null,
	domain = "general",
	enableOptimizer = true,
	enableHistory = true,
	enableFeatureSuggestions = true,
}) => {
	const form = new FormData();
	form.append("file", file);
	form.append("target_column_name", targetColumnName);
	form.append("problem_type", problemType);
	form.append("confirmed_drop_columns_json", JSON.stringify(confirmedDropColumns));
	form.append("enable_feature_engineering", String(enableFeatureEngineering));
	form.append("enable_discretization", String(enableDiscretization));
	form.append("enable_dim_reduction", String(enableDimReduction));
	form.append("domain", domain);
	form.append("enable_optimizer", String(enableOptimizer));
	form.append("enable_history", String(enableHistory));
	form.append("enable_feature_suggestions", String(enableFeatureSuggestions));
	if (dimReductionMethod) {
		form.append("dim_reduction_method", dimReductionMethod);
	}

	const { data } = await api.post("/clean", form, {
		headers: { "Content-Type": "multipart/form-data" },
	});
	return data;
};

export const getDownloadUrl = (relativeUrl) => `${API_BASE_URL}${relativeUrl}`;

export default api;
