"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  Clock,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function ApprovalPage() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [demoApproving, setDemoApproving] = useState(false);

  // Poll for status every 5 seconds
  useEffect(() => {
    if (!user?.id) return;
    const interval = setInterval(() => {
      refreshUser(user.id);
    }, 5000);
    return () => clearInterval(interval);
  }, [user?.id, refreshUser]);

  // Redirect if already approved
  useEffect(() => {
    if (user?.verification_status === "approved") {
      router.push("/dashboard");
    }
  }, [user?.verification_status, router]);

  const handleRefresh = async () => {
    if (!user?.id) return;
    setLoading(true);
    await refreshUser(user.id);
    setLoading(false);
  };

  const handleSimulateAdminApproval = async () => {
  if (!user?.id) return;

  setDemoApproving(true);

  try {
    // 1. Find this user's verification record
    const statusRes = await fetch(
      `${API_BASE_URL}/verification/status/${user.id}`
    );

    const status = await statusRes.json();

    if (!statusRes.ok || !status.verification?.id) {
      console.error("No verification found:", status);
      return;
    }

    const verificationId = status.verification.id;

    // 2. Approve using the verification ID and admin ID
    const res = await fetch(
      `${API_BASE_URL}/verification/admin/${verificationId}/approve?admin_id=eab2ec53-6553-4cee-88f9-7fbffa31fa03`,
      {
        method: "POST",
      }
    );

    const data = await res.json();
    console.log(data);

    if (res.ok) {
      await refreshUser(user.id);
    }
  } catch (e) {
    console.error("Demo approval error:", e);
  } finally {
    setDemoApproving(false);
  }
};

  return (
    <div className="max-w-2xl mx-auto py-12">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xl p-8 sm:p-12 text-center space-y-8">
        <div className="h-16 w-16 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto shadow-sm">
          <Clock className="h-8 w-8 animate-pulse" />
        </div>

        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-xs font-bold">
            <span>Status: Under Administrative Review</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            Your Student Verification is Under Review
          </h1>
          <p className="text-slate-600 text-sm max-w-lg mx-auto">
            Our campus administrators are reviewing your submitted admission letter and institutional credentials. Once verified, your SHA-256 hash is anchored on Quai Network and you receive +10 Trust Score.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left bg-slate-50 p-6 rounded-2xl border border-slate-200 text-xs">
          <div>
            <div className="font-bold text-slate-900">Estimated Processing Time</div>
            <div className="text-slate-600">&lt; 2 minutes (Hackathon Demo Mode)</div>
          </div>
          <div>
            <div className="font-bold text-slate-900">Current Trust Score</div>
            <div className="text-amber-700 font-bold">{user?.trust_score || 50} / 100 (Bronze Tier)</div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className="px-6 py-3 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-sm transition-all flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span>Check Approval Status</span>
          </button>

          <button
            type="button"
            onClick={handleSimulateAdminApproval}
            disabled={demoApproving}
            className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold text-sm shadow-md transition-all flex items-center gap-2"
          >
            {demoApproving ? (
              <>
                <div className="h-4 w-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                <span>Approving...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Simulate Instant Admin Approval</span>
              </>
            )}
          </button>
        </div>

        <div className="border-t border-slate-200 pt-6 text-xs text-slate-500">
          Want to explore while waiting?{" "}
          <Link href="/marketplace" className="text-primary-600 font-bold hover:underline">
            Browse Marketplace Catalog
          </Link>
        </div>
      </div>
    </div>
  );
}
