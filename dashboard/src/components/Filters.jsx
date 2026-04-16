import React from "react";

export default function Filters({ filters, options, onChange }) {
  return (
    <section className="filters" aria-label="Dashboard filters">
      <label>
        Date
        <select value={filters.date} onChange={(event) => onChange({ ...filters, date: event.target.value })}>
          <option value="all">All dates</option>
          {options.dates.map((date) => (
            <option key={date} value={date}>
              {date}
            </option>
          ))}
        </select>
      </label>
      <label>
        Test name
        <select value={filters.testName} onChange={(event) => onChange({ ...filters, testName: event.target.value })}>
          <option value="all">All tests</option>
          {options.testNames.map((testName) => (
            <option key={testName} value={testName}>
              {testName}
            </option>
          ))}
        </select>
      </label>
      <label>
        Error type
        <select value={filters.errorType} onChange={(event) => onChange({ ...filters, errorType: event.target.value })}>
          <option value="all">All errors</option>
          {options.errorTypes.map((errorType) => (
            <option key={errorType} value={errorType}>
              {errorType}
            </option>
          ))}
        </select>
      </label>
      <button type="button" onClick={() => onChange({ date: "all", testName: "all", errorType: "all" })}>
        Reset
      </button>
    </section>
  );
}
