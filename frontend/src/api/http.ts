const defaultApiBaseUrl = "http://127.0.0.1:8000";

export const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

export async function getJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = new URL(path, apiBaseUrl).toString();
  const response = await fetch(url, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}
