import React from "react";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, LineElement, PointElement, Filler, Tooltip, Legend);

const gridColor = "rgba(255,255,255,0.08)";
const tickColor = "#a8b3bd";

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: tickColor, boxWidth: 12, usePointStyle: true } },
    tooltip: {
      backgroundColor: "#101312",
      borderColor: "rgba(255,255,255,0.16)",
      borderWidth: 1,
      titleColor: "#ffffff",
      bodyColor: "#d9e5e1",
    },
  },
  scales: {
    x: { ticks: { color: tickColor }, grid: { color: gridColor } },
    y: { ticks: { color: tickColor }, grid: { color: gridColor }, beginAtZero: true },
  },
};

function EmptyChart({ title }) {
  return (
    <div className="chart-shell empty-state">
      <h2>{title}</h2>
      <p>Run the analytics pipeline to populate this chart.</p>
    </div>
  );
}

export function FlakyRankingChart({ rows }) {
  if (!rows.length) return <EmptyChart title="Flaky Test Ranking" />;

  return (
    <div className="chart-shell">
      <h2>Flaky Test Ranking</h2>
      <Bar
        options={baseOptions}
        data={{
          labels: rows.map((row) => row.test_name.replace("test_", "")),
          datasets: [
            {
              label: "Flakiness score",
              data: rows.map((row) => row.flakiness_score),
              backgroundColor: rows.map((row) => (row.risk === "high" ? "#ff5c7a" : row.risk === "medium" ? "#f5c542" : "#22d3a6")),
              borderRadius: 6,
            },
          ],
        }}
      />
    </div>
  );
}

export function TrendChart({ rows }) {
  if (!rows.length) return <EmptyChart title="Failure Trends" />;

  return (
    <div className="chart-shell">
      <h2>Failure Trends</h2>
      <Line
        options={{
          ...baseOptions,
          elements: { line: { tension: 0.35 } },
        }}
        data={{
          labels: rows.map((row) => row.date),
          datasets: [
            {
              label: "Failure rate",
              data: rows.map((row) => row.failure_rate),
              fill: true,
              borderColor: "#64e6ff",
              backgroundColor: "rgba(100,230,255,0.14)",
              pointBackgroundColor: "#64e6ff",
            },
            {
              label: "Avg execution time",
              data: rows.map((row) => row.avg_execution_time),
              borderColor: "#22d3a6",
              backgroundColor: "rgba(34,211,166,0.14)",
              pointBackgroundColor: "#22d3a6",
            },
          ],
        }}
      />
    </div>
  );
}

export function ErrorDistributionChart({ rows }) {
  if (!rows.length) return <EmptyChart title="Error Distribution" />;

  return (
    <div className="chart-shell">
      <h2>Error Distribution</h2>
      <Doughnut
        options={{ ...baseOptions, scales: undefined, cutout: "62%" }}
        data={{
          labels: rows.map((row) => row.error_type),
          datasets: [
            {
              data: rows.map((row) => row.count),
              backgroundColor: ["#ff5c7a", "#64e6ff", "#f5c542", "#22d3a6", "#f08cff"],
              borderColor: "#121615",
              borderWidth: 4,
            },
          ],
        }}
      />
    </div>
  );
}
