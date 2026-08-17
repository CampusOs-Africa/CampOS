"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
  phone?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  school?: string | null;
  faculty?: string | null;
  department?: string | null;
  level?: string | null;
  matric_number?: string | null;
  admission_year?: string | null;
  school_email?: string | null;
  student_id?: string | null;
  verification_status?: string;
  trust_score?: number;
  wallet_address?: string | null;
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<{ success: boolean; user?: AuthUser; error?: string }>;
  loginWithDemoUser: (userId: string) => Promise<{ success: boolean; user?: AuthUser; error?: string }>;
  register: (data: {
    name: string;
    email: string;
    password?: string;
    role?: string;
    school?: string;
    faculty?: string;
    department?: string;
    level?: string;
  }) => Promise<{ success: boolean; user?: AuthUser; error?: string }>;
  verifyOtp: (userId: string, email: string, otpCode: string) => Promise<{ success: boolean; error?: string }>;
  updateProfile: (
    data: Partial<{
      [K in keyof AuthUser]: AuthUser[K] | null;
    }> & {
      matricNumber?: string | null;
      dob?: string | null;
      admissionYear?: string | null;
    }
  ) => Promise<{ success: boolean; user?: AuthUser; error?: string }>;
  refreshUser: (userId?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "campusos_auth_user";
const TOKEN_KEY = "campusos_auth_token";
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((json) => {
        if (json?.id) {
          setUser(json);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(json));
        } else {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(STORAGE_KEY);
        }
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const saveAuth = useCallback((u: AuthUser, token: string) => {
    setUser(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    localStorage.setItem(TOKEN_KEY, token);
  }, []);

  const login = useCallback(
    async (email: string, password?: string) => {
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password: password ?? "",
          }),
        });
        const json = await res.json();
        if (!res.ok || !json.access_token || !json.user) {
          return {
            success: false,
            error:
              json?.detail ||
              json?.error?.message ||
              "Invalid email or password.",
          };
        }
        saveAuth(json.user, json.access_token);
        return { success: true, user: json.user };
      } catch (err: any) {
        return {
          success: false,
          error: "Network error. Make sure the CampusOS backend is running.",
        };
      }
    },
    [saveAuth]
  );

  const loginWithDemoUser = useCallback(
    async (userId: string) => {
      try {
        // One-click demo logins are a judge/demo convenience: they mint a JWT
        // for a seeded user via the demo-login endpoint (demo/test only).
        const res = await fetch(`${API_BASE}/auth/demo-login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });
        const json = await res.json();
        if (!res.ok || !json.access_token || !json.user) {
          return {
            success: false,
            error: `Demo account '${userId}' not found. Try starting backend with demo seeder enabled.`,
          };
        }
        saveAuth(json.user, json.access_token);
        return { success: true, user: json.user };
      } catch (err: any) {
        return {
          success: false,
          error: "Failed to connect to backend server.",
        };
      }
    },
    [saveAuth]
  );

  const register = useCallback(async (data: {
    name: string;
    email: string;
    password?: string;
    role?: string;
    school?: string;
    faculty?: string;
    department?: string;
    level?: string;
  }) => {
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          email: data.email.trim().toLowerCase(),
          password: data.password,
        }),
      });
      const json = await res.json();

      if (!res.ok || !json.access_token || !json.user) {
        return {
          success: false,
          error:
            json?.detail ||
            json?.error?.message ||
            "Registration failed. Email may already exist.",
        };
      }

      saveAuth(json.user, json.access_token);

      // School-email OTP verification is part of the optional student
      // verification flow later, not initial signup (any email is allowed).
      return { success: true, user: json.user };
    } catch (err: any) {
      return { success: false, error: "Network error during registration." };
    }
  }, [saveAuth]);

  const verifyOtp = useCallback(async (userId: string, email: string, otpCode: string) => {
    try {
      const res = await fetch(`${API_BASE}/verification/verify-email-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          email: email.trim().toLowerCase(),
          otp_code: otpCode.trim(),
        }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) {
        return {
          success: false,
          error: json?.detail || json?.error?.message || "Invalid or expired OTP code.",
        };
      }
      if (user) {
        const updated = { ...user, verification_status: "email_verified" };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        setUser(updated);
      }
      return { success: true };
    } catch (err: any) {
      return { success: false, error: "Network error verifying OTP." };
    }
  }, [user]);

  const updateProfile = useCallback(
    async (
      data: Partial<{
        [K in keyof AuthUser]: AuthUser[K] | null;
      }> & {
        matricNumber?: string | null;
        dob?: string | null;
        admissionYear?: string | null;
      }
    ) => {
      if (!user) return { success: false, error: "Not logged in" };
      const token = localStorage.getItem(TOKEN_KEY);
      try {
        // Map legacy camelCase field names used by the profile UI to the
        // snake_case fields the backend expects.
        const payload: Record<string, unknown> = { ...data };
        if ("matricNumber" in data) {
          payload.matric_number = (data as { matricNumber?: string | null }).matricNumber;
          delete payload.matricNumber;
        }
        if ("dob" in data) {
          payload.date_of_birth = (data as { dob?: string | null }).dob;
          delete payload.dob;
        }
        if ("admissionYear" in data) {
          payload.admission_year = (data as { admissionYear?: string | null }).admissionYear;
          delete payload.admissionYear;
        }
        const res = await fetch(`${API_BASE}/users/me`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (!res.ok) {
          return {
            success: false,
            error: json?.detail || json?.error?.message || "Failed to update profile.",
          };
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(json));
        setUser(json);
        return { success: true, user: json };
      } catch (err) {
        return { success: false, error: "Network error updating profile." };
      }
    },
    [user]
  );

  const refreshUser = useCallback(async (userId?: string) => {
    const targetId = userId || user?.id;
    if (!targetId) return;

    try {
      const userRes = await fetch(`${API_BASE}/users/${targetId}`);
      console.log("user status:", userRes.status);

      const latestUser = await userRes.json();
      console.log("latestUser:", latestUser);

      const verificationRes = await fetch(`${API_BASE}/verification/status/${targetId}`);
      console.log("verification status:", verificationRes.status);

      const verification = await verificationRes.json();
      console.log("verification:", verification);

      if (userRes.ok && verificationRes.ok) {
        const merged = {
          ...(user || {}),
          ...latestUser,
          verification_status: verification.verification_status,
          trust_score: verification.trust_score,
        };
        setUser(merged);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      }
    } catch (e) {
      console.error("Failed to refresh user:", e);
    }
  }, [user]);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        loginWithDemoUser,
        register,
        verifyOtp,
        updateProfile,
        refreshUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
