"use client";

// Centralized API configuration. The backend URL comes from the environment
// so production builds never embed localhost.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("campusos_auth_token");
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Authenticated JSON fetch. */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
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

/** Multipart/form-data fetch (no Content-Type so the browser sets boundary). */
export async function apiUpload<T>(
  path: string,
  formData: FormData,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    method: init.method || "POST",
    headers: { ...authHeaders(), ...(init.headers || {}) },
    body: formData,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg =
      (data as { detail?: string; error?: { message?: string } })?.detail ||
      (data as { error?: { message?: string } })?.error?.message ||
      "Upload failed";
    throw new ApiError(String(msg), res.status);
  }
  return data as T;
}
