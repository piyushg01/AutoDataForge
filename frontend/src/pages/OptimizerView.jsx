import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function OptimizerView({ optimization }) {
  return optimization?.results?.length ? (
    <Bar
      data={{
        labels: optimization.results.slice(0, 12).map((r) => r.variant),
        datasets: [{
          label: "Score",
          data: optimization.results.slice(0, 12).map((r) => r.score ?? 0),
          backgroundColor: "#60a5fa88",
          borderColor: "#2563eb",
          borderWidth: 1,
        }],
      }}
      options={{ plugins: { legend: { display: false } } }}
    />
  ) : <p style={{ color: "#64748b" }}>Run cleaning to generate optimizer results.</p>;
}
