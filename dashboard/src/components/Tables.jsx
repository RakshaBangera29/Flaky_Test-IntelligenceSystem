import React from "react";
import { pct, seconds } from "../lib/format";

export function SlowestTests({ rows }) {
  return (
    <section className="table-panel">
      <h2>Slowest Tests</h2>
      {!rows.length ? <p className="empty-copy">No slow test data yet.</p> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Test</th>
              <th>Module</th>
              <th>Avg</th>
              <th>P95</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 6).map((row) => (
              <tr key={row.test_name}>
                <td>{row.test_name}</td>
                <td>{row.module}</td>
                <td>{seconds(row.avg_execution_time)}</td>
                <td>{seconds(row.p95_execution_time)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function ModuleHealth({ rows }) {
  return (
    <section className="table-panel">
      <h2>Unstable Modules</h2>
      {!rows.length ? <p className="empty-copy">No module health data yet.</p> : null}
      <div className="module-list">
        {rows.map((row) => (
          <article className="module-row" key={row.module}>
            <div>
              <strong>{row.module}</strong>
              <span>{row.runs} runs</span>
            </div>
            <meter min="0" max="100" value={row.instability_rate} />
            <b>{pct(row.instability_rate)}</b>
          </article>
        ))}
      </div>
    </section>
  );
}

export function RecentRuns({ rows }) {
  return (
    <section className="table-panel wide">
      <h2>Recent Executions</h2>
      {!rows.length ? <p className="empty-copy">No executions match the current filters.</p> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Test</th>
              <th>Status</th>
              <th>Error</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 12).map((row) => (
              <tr key={row.id}>
                <td>{String(row.timestamp).replace("T", " ").slice(0, 19)}</td>
                <td>{row.test_name}</td>
                <td>
                  <span className={`status ${row.status}`}>{row.status}</span>
                </td>
                <td>{row.error_type}</td>
                <td>{seconds(row.execution_time)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
