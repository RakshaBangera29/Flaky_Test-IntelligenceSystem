import argparse
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "flaky_tests.sqlite"


SCENARIOS = [
    {
        "test_name": "test_login_valid_user",
        "module": "Authentication",
        "failure_rate": 0.13,
        "retry_rate": 0.10,
        "avg_time": 1.05,
        "errors": ["timeout", "locator issue", "api error", "assertion error"],
    },
    {
        "test_name": "test_search_returns_results",
        "module": "Search",
        "failure_rate": 0.18,
        "retry_rate": 0.16,
        "avg_time": 1.42,
        "errors": ["timeout", "api error", "locator issue"],
    },
    {
        "test_name": "test_feedback_form_submission",
        "module": "Forms",
        "failure_rate": 0.09,
        "retry_rate": 0.08,
        "avg_time": 0.94,
        "errors": ["api error", "timeout", "assertion error"],
    },
    {
        "test_name": "test_login_locked_user_message",
        "module": "Authentication",
        "failure_rate": 0.24,
        "retry_rate": 0.18,
        "avg_time": 1.31,
        "errors": ["locator issue", "timeout", "assertion error"],
    },
    {
        "test_name": "test_search_empty_state",
        "module": "Search",
        "failure_rate": 0.08,
        "retry_rate": 0.06,
        "avg_time": 0.82,
        "errors": ["timeout", "api error"],
    },
]


def init_db(reset):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        if reset:
            conn.execute("DROP TABLE IF EXISTS test_runs")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                module TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time REAL NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT,
                retry_count INTEGER NOT NULL,
                browser TEXT NOT NULL,
                environment TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )


def synthesize_run(index, total):
    scenario = random.choice(SCENARIOS)
    progress = index / max(total, 1)
    trend_pressure = 0.06 if scenario["module"] == "Authentication" and progress > 0.68 else 0
    fail_roll = random.random()
    retry_roll = random.random()

    if fail_roll < scenario["failure_rate"] + trend_pressure:
        status = "failed"
        error_type = random.choice(scenario["errors"])
        retry_count = 1
    elif retry_roll < scenario["retry_rate"] + trend_pressure / 2:
        status = "passed_on_retry"
        error_type = random.choice(scenario["errors"])
        retry_count = 1
    else:
        status = "passed"
        error_type = "none"
        retry_count = 0

    jitter = random.uniform(-0.28, 0.85)
    slow_multiplier = random.choice([1, 1, 1, 1.4, 1.8])
    execution_time = max(0.18, round((scenario["avg_time"] + jitter) * slow_multiplier, 3))
    base_time = datetime.now(timezone.utc) - timedelta(days=28)
    timestamp = base_time + timedelta(hours=index * 4, minutes=random.randint(0, 55))

    message = "" if error_type == "none" else f"Simulated {error_type} observed during {scenario['test_name']}"
    return (
        scenario["test_name"],
        scenario["module"],
        status,
        execution_time,
        error_type,
        message,
        retry_count,
        "chromium",
        random.choice(["qa", "staging", "nightly"]),
        timestamp.isoformat(),
    )


def generate(runs, seed, reset):
    if seed is not None:
        random.seed(seed)
    init_db(reset)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT INTO test_runs (
                test_name, module, status, execution_time, error_type, error_message,
                retry_count, browser, environment, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [synthesize_run(index, runs) for index in range(runs)],
        )
    print(f"Generated {runs} synthetic test executions in {DB_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Generate a realistic sample flaky-test dataset.")
    parser.add_argument("--runs", type=int, default=180)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--append", action="store_true", help="Append to existing data instead of resetting it.")
    args = parser.parse_args()
    generate(args.runs, args.seed, reset=not args.append)


if __name__ == "__main__":
    main()
