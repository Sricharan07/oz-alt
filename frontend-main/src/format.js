export function compactNumber(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) {
    return "0";
  }
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(number);
}

export function integer(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) {
    return "0";
  }
  return new Intl.NumberFormat("en").format(Math.round(number));
}

export function percent(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) {
    return "0.00";
  }
  return number.toFixed(2);
}

export function dateText(value) {
  if (!value) {
    return "Not recorded";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function bytes(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number) || number <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(number) / Math.log(1024)), units.length - 1);
  return `${(number / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function libraryId(row) {
  return `${row.vendor}/${row.library}`;
}

export function libraryPath(row) {
  return `/libraries/${encodeURIComponent(row.vendor)}/${String(row.library)
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/")}`;
}

export function statusClass(status) {
  return String(status || "").toLowerCase() === "up" || String(status || "").toLowerCase() === "operational"
    ? "ok"
    : "warn";
}
