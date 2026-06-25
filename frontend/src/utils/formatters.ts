export function formatDate(value: string | null | undefined) {
  if (!value) return "\u2014";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatShortDate(value: string | null | undefined) {
  if (!value) return "\u2014";
  return new Date(value).toLocaleDateString("pt-BR");
}

export function formatAuditDate(value: string | null | undefined) {
  if (!value) return "\u2014";
  return new Date(value).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export function formatMoney(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "Nao informado";
  const parsed = Number(value);
  return Number.isNaN(parsed)
    ? String(value)
    : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(parsed);
}

export function toNumberSafe(value: unknown, fallback = 0): number {
  const n = Number(value);
  return isFinite(n) ? n : fallback;
}

export function formatMoneySafe(value: unknown): string {
  const n = toNumberSafe(value);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatNumberSafe(value: unknown, decimals = 2): string {
  if (value === null || value === undefined) return "0";
  const n = toNumberSafe(value);
  return Number(n).toFixed(decimals);
}

export function formatPercentSafe(value: unknown, decimals = 1): string {
  if (value === null || value === undefined) return "0%";
  const n = toNumberSafe(value);
  return `${Number(n).toFixed(decimals)}%`;
}

export function formatDateTimeLocalInput(value: string | null | undefined) {
  if (!value) return "";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const timezoneOffset = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffset).toISOString().slice(0, 16);
}
