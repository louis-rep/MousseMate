import type { CheckIn, CheckInCreate, CheckInUpdate, StatsSummary } from "../types/checkin";

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API error ${response.status}: ${errorText || response.statusText}`
    );
  }

  // 204 No Content has no body
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listCheckins(skip = 0, limit = 20): Promise<CheckIn[]> {
  return request<CheckIn[]>(`/checkins?skip=${skip}&limit=${limit}`);
}

export function getCheckin(id: number): Promise<CheckIn> {
  return request<CheckIn>(`/checkins/${id}`);
}

export function createCheckin(data: CheckInCreate): Promise<CheckIn> {
  return request<CheckIn>("/checkins/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateCheckin(id: number, data: CheckInUpdate): Promise<CheckIn> {
  return request<CheckIn>(`/checkins/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteCheckin(id: number): Promise<void> {
  return request<void>(`/checkins/${id}`, { method: "DELETE" });
}

export function getStatsSummary(): Promise<StatsSummary> {
  return request<StatsSummary>("/checkins/stats/summary");
}
