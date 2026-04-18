import { useEffect, useMemo, useState } from "react";
import { unique } from "./format";

function normalizeMetrics(payload) {
  const rawRuns = Array.isArray(payload?.raw_runs) ? payload.raw_runs : [];
  const normalizedRuns = rawRuns.map((run, index) => {
    const timestamp = String(run?.timestamp || "");
    const date = String(run?.date || (timestamp.includes("T") ? timestamp.split("T")[0] : ""));
    return {
      id: run?.id ?? `${timestamp}-${index}`,
      test_name: String(run?.test_name || "unknown_test"),
      status: String(run?.status || "unknown"),
      error_type: String(run?.error_type || "none"),
      execution_time: Number(run?.execution_time || 0),
      timestamp,
      date,
    };
  });

  return {
    summary: {
      total_runs: Number(payload?.summary?.total_runs || normalizedRuns.length),
      failed_runs: Number(payload?.summary?.failed_runs || 0),
      unstable_runs: Number(payload?.summary?.unstable_runs || 0),
      failure_rate: Number(payload?.summary?.failure_rate || 0),
      average_execution_time: Number(payload?.summary?.average_execution_time || 0),
      last_updated: String(payload?.summary?.last_updated || ""),
    },
    insights: Array.isArray(payload?.insights) ? payload.insights : [],
    rankings: Array.isArray(payload?.rankings) ? payload.rankings : [],
    trends: Array.isArray(payload?.trends) ? payload.trends : [],
    error_distribution: Array.isArray(payload?.error_distribution) ? payload.error_distribution : [],
    modules: Array.isArray(payload?.modules) ? payload.modules : [],
    slowest_tests: Array.isArray(payload?.slowest_tests) ? payload.slowest_tests : [],
    raw_runs: normalizedRuns,
  };
}

export function useMetrics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(import.meta.env.BASE_URL + "data/metrics.json")
      .then((response) => {
        if (!response.ok) throw new Error("Dashboard data was not found.");
        return response.json();
      })
      .then((payload) => setData(normalizeMetrics(payload)))
      .catch((err) => setError(err.message));
  }, []);

  const options = useMemo(() => {
    if (!data) return { testNames: [], errorTypes: [], dates: [] };
    return {
      testNames: unique(data.raw_runs.map((run) => run.test_name)),
      errorTypes: unique(data.raw_runs.map((run) => run.error_type).filter((type) => type !== "none")),
      dates: unique(data.raw_runs.map((run) => run.date).filter(Boolean)),
    };
  }, [data]);

  return { data, error, options };
}
