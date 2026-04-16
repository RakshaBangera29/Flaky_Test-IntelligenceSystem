# Flaky Test Intelligence System

A full-stack QA Automation and Data Analytics portfolio project that simulates flaky UI tests, stores execution history in SQLite, processes metrics with Pandas, and presents an interactive React dashboard.

## What It Demonstrates

- QA automation thinking: login, search, and form submission test flows.
- Flaky test simulation: random failures, slow responses, timeouts, locator issues, and API errors.
- Data engineering: structured SQLite storage plus CSV/JSON exports.
- Analytics: flakiness score, failure rate, average duration, failure categories, trends, unstable modules, and prediction flags.
- Dashboarding: dark, AI-inspired React UI with filters, charts, rankings, and automated insights.

## Project Structure

```text
flaky-test-intelligence-system/
  qa_flaky_intel/
    automation/
      sample_app.py          # tiny local web app used by Playwright tests
      run_tests.py           # simulated Playwright test runner and logger
    pipeline/
      process_results.py     # Pandas analytics pipeline
    data/
      flaky_tests.sqlite     # generated SQLite database
      test_runs.csv          # generated raw execution export
      metrics.json           # generated dashboard analytics
  dashboard/
    src/
      App.jsx
      components/
      lib/
      styles.css
    public/data/metrics.json # dashboard-ready analytics
  requirements.txt
```

## Quick Start

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m qa_flaky_intel.automation.run_tests --runs 60
python -m qa_flaky_intel.pipeline.process_results
cd dashboard
npm install
npm run dev
```

Open the local Vite URL shown in your terminal.

If Playwright browser binaries are not available yet, create the showcase dataset without launching a browser:

```bash
python -m qa_flaky_intel.automation.generate_sample_data --runs 180 --seed 7
python -m qa_flaky_intel.pipeline.process_results
```

## Generate More Data

```bash
python -m qa_flaky_intel.automation.run_tests --runs 150 --seed 42
python -m qa_flaky_intel.pipeline.process_results
```

The pipeline writes:

- `qa_flaky_intel/data/test_runs.csv`
- `qa_flaky_intel/data/metrics.json`
- `dashboard/public/data/metrics.json`

## Analytics Logic

The flakiness score combines:

- failure rate,
- retry pass rate,
- execution time volatility,
- recent failures,
- failure reason diversity.

Tests with a score of `70+` are flagged as high risk. The dashboard automatically highlights unstable tests, slow tests, and rising failure trends.

## Notes

The runner uses Playwright with Python and a tiny local HTTP app. It intentionally injects random delays and failure modes to create realistic flaky test telemetry without requiring external services.
