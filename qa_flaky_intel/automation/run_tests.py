import argparse
import random
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from qa_flaky_intel.automation.sample_app import start_demo_server


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "flaky_tests.sqlite"


@dataclass(frozen=True)
class TestScenario:
    name: str
    module: str
    base_failure_rate: float
    slow_rate: float
    timeout_rate: float
    locator_rate: float
    api_error_rate: float


SCENARIOS = [
    TestScenario("test_login_valid_user", "Authentication", 0.16, 0.22, 0.08, 0.04, 0.04),
    TestScenario("test_search_returns_results", "Search", 0.21, 0.30, 0.11, 0.06, 0.04),
    TestScenario("test_feedback_form_submission", "Forms", 0.12, 0.18, 0.05, 0.03, 0.04),
    TestScenario("test_login_locked_user_message", "Authentication", 0.28, 0.26, 0.12, 0.09, 0.07),
    TestScenario("test_search_empty_state", "Search", 0.10, 0.16, 0.04, 0.03, 0.03),
]


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
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


def choose_failure(scenario):
    roll = random.random()
    if roll > scenario.base_failure_rate:
        return None

    failure_roll = random.random()
    if failure_roll < scenario.timeout_rate:
        return "timeout"
    if failure_roll < scenario.timeout_rate + scenario.locator_rate:
        return "locator issue"
    if failure_roll < scenario.timeout_rate + scenario.locator_rate + scenario.api_error_rate:
        return "api error"
    return "assertion error"


def run_login(page, scenario, failure_type):
    page.goto("http://127.0.0.1:8765/")
    page.fill("#email", "qa.analyst@example.com")
    page.fill("#password", "correct-horse-battery-staple")
    if failure_type == "locator issue":
        page.click("#signin-btn", timeout=350)
    page.click("#login-btn")
    if failure_type == "timeout":
        page.wait_for_selector("#login-result >> text=Welcome", timeout=1)
    else:
        page.wait_for_selector("#login-result >> text=Welcome", timeout=1000)
    if failure_type == "assertion error":
        raise AssertionError("Expected welcome text to include a session id")


def run_search(page, scenario, failure_type):
    page.goto("http://127.0.0.1:8765/")
    page.fill("#search-box", "wireless keyboard")
    if failure_type == "api error":
        raise RuntimeError("Search API returned HTTP 503")
    if failure_type == "locator issue":
        page.click("#search-submit", timeout=350)
    page.click("#search-btn")
    if failure_type == "timeout":
        page.wait_for_selector("#search-result >> text=Showing results", timeout=1)
    else:
        page.wait_for_selector("#search-result >> text=Showing results", timeout=1200)
    if failure_type == "assertion error":
        raise AssertionError("Expected at least five search results")


def run_form(page, scenario, failure_type):
    page.goto("http://127.0.0.1:8765/")
    page.fill("#name", "QA Analyst")
    page.fill("#message", "This workflow is ready for regression coverage.")
    if failure_type == "api error":
        raise RuntimeError("Feedback API rejected payload")
    if failure_type == "locator issue":
        page.click("#send-feedback", timeout=350)
    page.click("#submit-btn")
    if failure_type == "timeout":
        page.wait_for_selector("#form-result >> text=Feedback submitted", timeout=1)
    else:
        page.wait_for_selector("#form-result >> text=Feedback submitted", timeout=1000)
    if failure_type == "assertion error":
        raise AssertionError("Expected confirmation email event")


def execute_scenario(page, scenario):
    failure_type = choose_failure(scenario)
    if random.random() < scenario.slow_rate:
        time.sleep(random.uniform(0.3, 1.2))

    if "login" in scenario.name:
        run_login(page, scenario, failure_type)
    elif "search" in scenario.name:
        run_search(page, scenario, failure_type)
    else:
        run_form(page, scenario, failure_type)
    return failure_type


def normalize_error(exc):
    if exc is None:
        return "none", ""
    message = str(exc)
    if isinstance(exc, PlaywrightTimeoutError) or "Timeout" in message:
        return "timeout", message[:240]
    if "strict mode violation" in message or "waiting for locator" in message or "signin-btn" in message:
        return "locator issue", message[:240]
    if "API" in message or "HTTP 503" in message:
        return "api error", message[:240]
    if isinstance(exc, AssertionError):
        return "assertion error", message[:240]
    return "unknown", message[:240]


def insert_result(result):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO test_runs (
                test_name, module, status, execution_time, error_type, error_message,
                retry_count, browser, environment, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["test_name"],
                result["module"],
                result["status"],
                result["execution_time"],
                result["error_type"],
                result["error_message"],
                result["retry_count"],
                result["browser"],
                result["environment"],
                result["timestamp"],
            ),
        )


def run_suite(total_runs, seed=None):
    if seed is not None:
        random.seed(seed)

    init_db()
    server = start_demo_server()
    base_time = datetime.now(timezone.utc) - timedelta(days=21)
    generated = 0

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()

            for run_index in range(total_runs):
                scenario = random.choice(SCENARIOS)
                started = time.perf_counter()
                status = "passed"
                error_type = "none"
                error_message = ""
                retry_count = 0

                try:
                    execute_scenario(page, scenario)
                except Exception as exc:
                    first_error_type, first_message = normalize_error(exc)
                    retry_count = 1
                    try:
                        page.reload()
                        execute_scenario(page, scenario)
                        status = "passed_on_retry"
                        error_type = first_error_type
                        error_message = f"Recovered on retry after {first_error_type}: {first_message}"
                    except Exception as retry_exc:
                        status = "failed"
                        error_type, error_message = normalize_error(retry_exc)

                execution_time = round(time.perf_counter() - started, 3)
                timestamp = base_time + timedelta(
                    minutes=run_index * random.randint(9, 42),
                    seconds=random.randint(0, 59),
                )

                insert_result(
                    {
                        "test_name": scenario.name,
                        "module": scenario.module,
                        "status": status,
                        "execution_time": execution_time,
                        "error_type": error_type,
                        "error_message": error_message,
                        "retry_count": retry_count,
                        "browser": "chromium",
                        "environment": random.choice(["staging", "qa", "nightly"]),
                        "timestamp": timestamp.isoformat(),
                    }
                )
                generated += 1

            browser.close()
    finally:
        server.shutdown()

    print(f"Logged {generated} test executions to {DB_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Run flaky Playwright simulations.")
    parser.add_argument("--runs", type=int, default=100, help="Number of test executions to simulate.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    args = parser.parse_args()
    run_suite(args.runs, args.seed)


if __name__ == "__main__":
    main()
