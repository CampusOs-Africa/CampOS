"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Mail,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyOtp, user } = useAuth();

  const userId = searchParams?.get("userId") || user?.id || "";
  const email = searchParams?.get("email") || user?.email || "";

  const [otpCode, setOtpCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.trim().length !== 6) {
      setError("Please enter a 6-digit OTP code.");
      return;
    }

    setLoading(true);
    setError(null);

    const res = await verifyOtp(userId, email, otpCode);

    setLoading(false);

    if (!res.success) {
      setError(res.error || "Invalid or expired OTP code.");
      return;
    }

    setSuccessMsg("Email verification successful! Proceeding to Profile Completion...");
    setTimeout(() => {
      router.push(`/create-profile?userId=${encodeURIComponent(userId)}`);
    }, 1200);
  };

  const handleResend = async () => {
    if (countdown > 0 || !userId || !email) return;
    setResendLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/verification/send-email-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, email }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) {
        setError(json?.detail || json?.error?.message || "Failed to resend OTP code.");
      } else {
        setSuccessMsg("A new 6-digit OTP code has been sent to your email.");
        setCountdown(60); // 60s resend cooldown
      }
    } catch (e) {
      setError("Network error resending OTP code.");
    } finally {
      setResendLoading(false);
    }
  };

  const handleFillDemoOtp = () => {
    // When USE_MOCK_EMAIL_OTP=True in backend, 123456 works
    setOtpCode("123456");
    setError(null);
  };

  return (
    <div className="max-w-xl mx-auto py-12">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-8 text-white text-center space-y-2">
          <div className="h-12 w-12 rounded-2xl bg-primary-500/20 border border-primary-500/40 text-primary-400 flex items-center justify-center mx-auto mb-2">
            <Mail className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Verify Your University Email
          </h1>
          <p className="text-xs text-slate-300">
            We sent a 6-digit institutional verification code to:
          </p>
          <div className="font-mono font-bold text-sm bg-slate-800/80 px-3 py-1.5 rounded-lg inline-block text-primary-300 border border-slate-700">
            {email || "your-email@edu.ng"}
          </div>
        </div>

        {/* Body */}
        <div className="p-8 space-y-6">
          {error && (
            <div
              className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-start gap-3"
              role="alert"
            >
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <strong className="font-bold">Verification Error: </strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          {successMsg && (
            <div
              className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm flex items-start gap-3"
              role="status"
            >
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="font-bold">Success: </strong>
                <span>{successMsg}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleVerify} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 text-center">
                Enter 6-Digit OTP Code
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
                className="w-full text-center font-mono text-2xl tracking-[0.5em] px-4 py-3 rounded-xl border-2 border-slate-300 focus:outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-500/20"
              />
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full py-3.5 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:bg-primary-300 text-white font-bold text-sm shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <>
                  <span>Verify Email & Continue</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Hackathon Demo Helper */}
          <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-amber-800">
              <Sparkles className="h-4 w-4 text-amber-600 shrink-0" />
              <span>
                <strong>Hackathon Demo Mode:</strong> Default mock OTP is <code className="bg-amber-100 px-1.5 py-0.5 rounded font-bold">123456</code>.
              </span>
            </div>
            <button
              type="button"
              onClick={handleFillDemoOtp}
              className="px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold rounded-lg transition-colors shrink-0"
            >
              Auto-Fill
            </button>
          </div>

          <div className="border-t border-slate-200 pt-4 flex items-center justify-between text-xs">
            <span className="text-slate-500">Didn't receive the code?</span>
            <button
              type="button"
              onClick={handleResend}
              disabled={countdown > 0 || resendLoading}
              className="inline-flex items-center gap-1.5 text-primary-600 font-bold hover:underline disabled:text-slate-400 disabled:no-underline"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${resendLoading ? "animate-spin" : ""}`} />
              <span>
                {countdown > 0
                  ? `Resend available in ${countdown}s`
                  : resendLoading
                  ? "Sending..."
                  : "Resend Code"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="text-center py-20">Loading OTP Verification...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
