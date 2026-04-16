export function pct(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

export function seconds(value) {
  return `${Number(value || 0).toFixed(2)}s`;
}

export function compact(value) {
  return new Intl.NumberFormat("en", { notation: "compact" }).format(value || 0);
}

export function unique(values) {
  return [...new Set(values.filter(Boolean))].sort();
}
