import type { Token, UserRead } from "../types/auth";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

async function request<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function login(username: string, password: string): Promise<Token> {
  return request<Token>("/auth/login", { username, password });
}

export function register(username: string, password: string): Promise<UserRead> {
  return request<UserRead>("/auth/register", { username, password });
}

export async function getMe(): Promise<UserRead> {
  const token = localStorage.getItem("access_token");
  const r = await fetch(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return r.json() as Promise<UserRead>;
}
