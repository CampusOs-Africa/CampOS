"use client";

// Authenticated admin API helper. Identity/authorization is enforced by the
// backend via require_admin; this client only attaches the JWT.

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("campusos_auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function adminFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(init.headers || {}),
    },
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg =
      (data && (data as { detail?: string; error?: { message?: string } }).detail) ||
      (data && (data as { error?: { message?: string } }).error?.message) ||
      `Request failed (${res.status})`;
    throw new ApiError(String(msg), res.status);
  }
  return data as T;
}

export const isAdmin = (user: { role?: string } | null): boolean =>
  user?.role === "admin";
