import type { UserRead } from "../types/auth";
import type { UserSearchResult } from "../types/user";

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

  if (response.status === 204 || response.status === 201) return undefined as T;

  return response.json() as Promise<T>;
}

export function searchUsers(q: string): Promise<UserSearchResult[]> {
  return request<UserSearchResult[]>(`/users/search?q=${encodeURIComponent(q)}`);
}

export function listMates(): Promise<UserRead[]> {
  return request<UserRead[]>("/mates");
}

export function followUser(userId: number): Promise<void> {
  return request<void>(`/follow/${userId}`, { method: "POST" });
}

export function unfollowUser(userId: number): Promise<void> {
  return request<void>(`/unfollow/${userId}`, { method: "DELETE" });
}
