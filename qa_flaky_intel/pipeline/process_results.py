import json
import shutil
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "flaky_tests.sqlite"
CSV_PATH = DATA_DIR / "test_runs.csv"
METRICS_PATH = DATA_DIR / "metrics.json"
DASHBOARD_METRICS_PATH = ROOT / "dashboard" / "public" / "data" / "metrics.json"


def load_results():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No SQLite database found at {DB_PATH}. Run the automation first.")

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM test_runs", conn, parse_dates=["timestamp"])


def score_flakiness(group):
    total = len(group)
    failures = (group["status"] == "failed").sum()
    retry_passes = (group["status"] == "passed_on_retry").sum()
    failure_rate = failures / total
    retry_pass_rate = retry_passes / total
    duration_cv = group["execution_time"].std(ddof=0) / max(group["execution_time"].mean(), 0.001)
    recent = group.sort_values("timestamp").tail(max(3, total // 4))
    recent_failure_rate = (recent["status"] != "passed").mean()
    error_diversity = group.loc[group["error_type"] != "none", "error_type"].nunique() / 4
    return min(
        100,
        round(
            (failure_rate * 40)
            + (retry_pass_rate * 20)
            + (min(duration_cv, 1.5) / 1.5 * 15)
            + (recent_failure_rate * 15)
            + (error_diversity * 10),
            1,
        ),
    )


def risk_label(score):
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def build_metrics(df):
    df = df.copy()
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["is_failure"] = df["status"].eq("failed")
    df["is_unstable"] = df["status"].ne("passed")

    grouped = df.groupby(["test_name", "module"], as_index=False).agg(
        runs=("id", "count"),
        failures=("is_failure", "sum"),
        unstable_runs=("is_unstable", "sum"),
        avg_execution_time=("execution_time", "mean"),
        max_execution_time=("execution_time", "max"),
        retry_passes=("status", lambda values: (values == "passed_on_retry").sum()),
    )

    scores = (
        df.groupby(["test_name", "module"])
        .apply(score_flakiness, include_groups=False)
        .reset_index(name="flakiness_score")
    )

    rankings = grouped.merge(scores, on=["test_name", "module"])
    rankings["failure_rate"] = (rankings["failures"] / rankings["runs"] * 100).round(1)
    rankings["avg_execution_time"] = rankings["avg_execution_time"].round(3)
    rankings["max_execution_time"] = rankings["max_execution_time"].round(3)
    rankings["risk"] = rankings["flakiness_score"].apply(risk_label)
    rankings["predicted_flaky"] = rankings["flakiness_score"].ge(55)
    rankings = rankings.sort_values("flakiness_score", ascending=False)

    trends = (
        df.groupby("date", as_index=False)
        .agg(
            runs=("id", "count"),
            failures=("is_failure", "sum"),
            unstable_runs=("is_unstable", "sum"),
            avg_execution_time=("execution_time", "mean"),
        )
        .sort_values("date")
    )
    trends["failure_rate"] = (trends["failures"] / trends["runs"] * 100).round(1)
    trends["avg_execution_time"] = trends["avg_execution_time"].round(3)

    error_distribution = (
        df[df["error_type"] != "none"]
        .groupby("error_type", as_index=False)
        .agg(count=("id", "count"))
        .sort_values("count", ascending=False)
    )

    modules = (
        df.groupby("module", as_index=False)
        .agg(runs=("id", "count"), unstable_runs=("is_unstable", "sum"), avg_execution_time=("execution_time", "mean"))
        .sort_values("unstable_runs", ascending=False)
    )
    modules["instability_rate"] = (modules["unstable_runs"] / modules["runs"] * 100).round(1)
    modules["avg_execution_time"] = modules["avg_execution_time"].round(3)

    slowest = (
        df.groupby(["test_name", "module"], as_index=False)
        .agg(avg_execution_time=("execution_time", "mean"), p95_execution_time=("execution_time", lambda s: s.quantile(0.95)))
        .sort_values("p95_execution_time", ascending=False)
    )
    slowest["avg_execution_time"] = slowest["avg_execution_time"].round(3)
    slowest["p95_execution_time"] = slowest["p95_execution_time"].round(3)

    insights = generate_insights(rankings, trends, modules, error_distribution)

    return {
        "summary": {
            "total_runs": int(len(df)),
            "failed_runs": int(df["is_failure"].sum()),
            "unstable_runs": int(df["is_unstable"].sum()),
            "failure_rate": round(float(df["is_failure"].mean() * 100), 1),
            "average_execution_time": round(float(df["execution_time"].mean()), 3),
            "last_updated": pd.Timestamp.utcnow().isoformat(),
        },
        "rankings": rankings.to_dict(orient="records"),
        "trends": trends.to_dict(orient="records"),
        "error_distribution": error_distribution.to_dict(orient="records"),
        "modules": modules.to_dict(orient="records"),
        "slowest_tests": slowest.to_dict(orient="records"),
        "raw_runs": df.sort_values("timestamp", ascending=False).head(500).assign(timestamp=lambda x: x["timestamp"].astype(str)).to_dict(orient="records"),
        "insights": insights,
    }


def generate_insights(rankings, trends, modules, errors):
    insights = []
    if not rankings.empty:
        top = rankings.iloc[0]
        if top["flakiness_score"] >= 70:
            insights.append(f"{top['test_name']} is highly unstable with a flakiness score of {top['flakiness_score']}.")
        else:
            insights.append(f"{top['test_name']} is the current top flaky candidate and should stay on the watchlist.")

    if len(trends) >= 4:
        previous = trends.tail(4).head(2)["failure_rate"].mean()
        current = trends.tail(2)["failure_rate"].mean()
        if current > previous + 5:
            insights.append(f"Failure rate is rising in the latest runs: {round(current, 1)}% versus {round(previous, 1)}%.")
        else:
            insights.append("Recent failure trend is stable, but retry recoveries still indicate hidden instability.")

    if not modules.empty:
        module = modules.iloc[0]
        insights.append(f"{module['module']} is the most unstable module at {module['instability_rate']}% unstable runs.")

    if not errors.empty:
        error = errors.iloc[0]
        insights.append(f"{error['error_type'].title()} is the leading failure reason and appears {int(error['count'])} times.")

    return insights


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = load_results()
    df.to_csv(CSV_PATH, index=False)
    metrics = build_metrics(df)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    DASHBOARD_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(METRICS_PATH, DASHBOARD_METRICS_PATH)
    print(f"Processed {len(df)} rows")
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {METRICS_PATH}")
    print(f"Copied dashboard data to {DASHBOARD_METRICS_PATH}")


if __name__ == "__main__":
    main()
