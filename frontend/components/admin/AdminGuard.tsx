"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ShieldAlert, Loader2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted || isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-500">
        <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto py-20 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-amber-500" />
        <h2 className="mt-3 text-lg font-bold text-slate-900">Sign in required</h2>
        <p className="mt-1 text-sm text-slate-500">
          Please log in with an administrator account.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-block rounded-xl bg-primary-600 px-4 py-2 text-sm font-bold text-white"
        >
          Go to login
        </Link>
      </div>
    );
  }

  if (user.role !== "admin") {
    return (
      <div className="max-w-md mx-auto py-20 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-red-500" />
        <h2 className="mt-3 text-lg font-bold text-slate-900">Access denied</h2>
        <p className="mt-1 text-sm text-slate-500">
          This area is restricted to CampusOS administrators.
        </p>
        <Link
          href="/marketplace"
          className="mt-4 inline-block rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white"
        >
          Back to marketplace
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
