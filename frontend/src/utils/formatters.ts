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

export function formatDateTimeLocalInput(value: string | null | undefined) {
  if (!value) return "";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const timezoneOffset = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffset).toISOString().slice(0, 16);
}
