"use client";

import React from "react";
import { AdminGuard } from "../../components/admin/AdminGuard";
import { AdminNav } from "../../components/admin/AdminNav";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <div className="space-y-6 py-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
            Admin Operations
          </h1>
          <p className="text-sm text-slate-500">
            Verification, moderation, trust, and marketplace health. The backend
            enforces administrator authorization on every action.
          </p>
        </div>
        <AdminNav />
        {children}
      </div>
    </AdminGuard>
  );
}
