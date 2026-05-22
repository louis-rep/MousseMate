import type { Entry, EntryCreate, EntryUpdate, StatsSummary, Venue } from "../types/entry";

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

  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

export function listEntries(): Promise<Venue[]> {
  return request<Venue[]>("/entries");
}

export function getEntry(id: number): Promise<Entry> {
  return request<Entry>(`/entry/${id}`);
}

export function createEntry(data: EntryCreate): Promise<Entry> {
  return request<Entry>("/entry", { method: "POST", body: JSON.stringify(data) });
}

export function updateEntry(id: number, data: EntryUpdate): Promise<Entry> {
  return request<Entry>(`/entry/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteEntry(id: number): Promise<void> {
  return request<void>(`/entry/${id}`, { method: "DELETE" });
}

export function getStatsSummary(): Promise<StatsSummary> {
  return request<StatsSummary>("/entry/stats/summary");
}
