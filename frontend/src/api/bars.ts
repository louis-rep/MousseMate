import type { Bar } from "../types/bar";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
    ...init,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function searchBars(q: string): Promise<Bar[]> {
  return request<Bar[]>(`/bars?q=${encodeURIComponent(q)}`);
}
