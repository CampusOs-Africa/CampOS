"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  ShieldCheck,
  Lock,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { UploadForm } from "../../components/verification/UploadForm";

export default function UploadIdPage() {
  const router = useRouter();
  const { user } = useAuth();

  const handleUploadSuccess = () => {
    // Navigate to approval status page
    router.push("/approval");
  };

  return (
    <div className="max-w-3xl mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-3xl p-8 text-white shadow-xl space-y-2 border border-slate-700/50">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/40 text-primary-400 text-xs font-semibold">
          <ShieldCheck className="h-4 w-4" />
          <span>Student Onboarding Step 3 of 3 — KYC Verification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          Upload Student ID or Admission Letter
        </h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Your documents are validated against OWASP magic byte spoofing and stored securely in Cloudinary. Only a 32-byte SHA-256 hash is anchored on Quai Network.
        </p>
      </div>

      {/* Upload Form Component */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8">
        <UploadForm
          onSuccess={handleUploadSuccess}
          schoolEmail={user?.school_email ?? null}
        />
      </div>
    </div>
  );
}
