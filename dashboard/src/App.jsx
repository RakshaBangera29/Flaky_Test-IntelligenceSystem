import React, { useMemo, useState } from "react";
import { ErrorDistributionChart, FlakyRankingChart, TrendChart } from "./components/Charts.jsx";
import Filters from "./components/Filters.jsx";
import MetricTile from "./components/MetricTile.jsx";
import { ModuleHealth, RecentRuns, SlowestTests } from "./components/Tables.jsx";
import { compact, pct, seconds } from "./lib/format.js";
import { useMetrics } from "./lib/useMetrics.js";

const emptyFilters = { date: "all", testName: "all", errorType: "all" };

function filterRuns(rows, filters) {
  return rows.filter((row) => {
    const matchesDate = filters.date === "all" || row.date === filters.date;
    const matchesTest = filters.testName === "all" || row.test_name === filters.testName;
    const matchesError = filters.errorType === "all" || row.error_type === filters.errorType;
    return matchesDate && matchesTest && matchesError;
  });
}

function deriveFilteredSummary(rows) {
  const total = rows.length;
  const failed = rows.filter((row) => row.status === "failed").length;
  const unstable = rows.filter((row) => row.status !== "passed").length;
  const avg = total ? rows.reduce((sum, row) => sum + Number(row.execution_time || 0), 0) / total : 0;
  return { total, failed, unstable, failureRate: total ? (failed / total) * 100 : 0, avg };
}

export default function App() {
  const { data, error, options } = useMetrics();
  const [filters, setFilters] = useState(emptyFilters);

  const filteredRuns = useMemo(() => (data ? filterRuns(data.raw_runs || [], filters) : []), [data, filters]);
  const filteredSummary = useMemo(() => deriveFilteredSummary(filteredRuns), [filteredRuns]);

  if (error) {
    return <main className="app-state">Run the analytics pipeline first. {error}</main>;
  }

  if (!data) {
    return <main className="app-state">Loading flaky test intelligence...</main>;
  }

  return (
    <main className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">QA Automation + Data Analytics</p>
          <h1>Flaky Test Intelligence System</h1>
          <p className="intro">
            Detect unstable tests, explain recurring failure patterns, and prioritize the automation suite by reliability risk.
          </p>
        </div>
        <aside className="insight-panel">
          <span>Auto Insights</span>
          {data.insights.length ? data.insights.map((insight) => <p key={insight}>{insight}</p>) : <p>No insights generated yet.</p>}
        </aside>
      </header>

      <Filters filters={filters} options={options} onChange={setFilters} />

      <section className="metrics-grid">
        <MetricTile label="Filtered Runs" value={compact(filteredSummary.total)} hint={`${compact(data.summary.total_runs)} total stored`} />
        <MetricTile label="Failure Rate" value={pct(filteredSummary.failureRate)} hint={`${compact(filteredSummary.failed)} failed executions`} />
        <MetricTile label="Unstable Runs" value={compact(filteredSummary.unstable)} hint="failures and retry recoveries" />
        <MetricTile label="Avg Runtime" value={seconds(filteredSummary.avg)} hint={`${seconds(data.summary.average_execution_time)} overall`} />
      </section>

      <section className="chart-grid">
        <FlakyRankingChart rows={(data.rankings || []).slice(0, 7)} />
        <TrendChart rows={data.trends || []} />
        <ErrorDistributionChart rows={data.error_distribution || []} />
      </section>

      <section className="lower-grid">
        <SlowestTests rows={data.slowest_tests || []} />
        <ModuleHealth rows={data.modules || []} />
        <RecentRuns rows={filteredRuns} />
      </section>
    </main>
  );
}
