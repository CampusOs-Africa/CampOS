"use client";

import React from "react";
import { UploadForm } from "../../../components/verification/UploadForm";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../../../context/AuthContext";

export default function UploadPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Student Identity Verification
          </h1>
          <p className="text-sm text-slate-500">
            Submit your school email and documents for administrative review.
            Your identity is confirmed from your account — no ID needs to be entered.
          </p>
        </div>
        {user && (
          <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span className="text-xs text-slate-600">
              Signed in as <strong>{user.email}</strong>
            </span>
          </div>
        )}
      </div>

      <UploadForm schoolEmail={user?.school_email ?? null} />
    </div>
  );
}
