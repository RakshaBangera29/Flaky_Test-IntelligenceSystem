import React from "react";

export default function MetricTile({ label, value, hint }) {
  return (
    <section className="metric-tile">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{hint}</span>
    </section>
  );
}
