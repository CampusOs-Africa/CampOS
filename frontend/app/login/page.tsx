"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  LogIn,
  Mail,
  Lock,
  AlertCircle,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Eye,
  EyeOff,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginWithDemoUser } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError("Please enter your university email.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    setError(null);

    const res = await login(email.trim(), password);

    setLoading(false);

    // if (!res.success || !res.user) {
    //   setError(res.error || "User with this email not found. Please Sign Up.");
    //   return;
    // }
    
    // update to the above logic to redirect based on user role
    if (res.success) {
      router.push(res.user?.role === "admin" ? "/admin" : "/dashboard");
      router.refresh();
    } else {
      setError(res.error || "Invalid email or password.");
    }

    // // Redirect to dashboard on login success
    // router.push("/dashboard");
  };

  const handleDemoLogin = async (id: string) => {
    setLoading(true);
    setError(null);
    const res = await loginWithDemoUser(id);
    setLoading(false);
    if (res.success) {
      router.push(res.user?.role === "admin" ? "/admin" : "/dashboard");
      router.refresh();
    } else {
      setError(res.error || "Invalid email or password.");
    }
  };

  return (
    <div className="max-w-xl mx-auto py-12">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-8 text-white text-center space-y-2">
          <div className="h-12 w-12 rounded-2xl bg-primary-500/20 border border-primary-500/40 text-primary-400 flex items-center justify-center mx-auto mb-2">
            <LogIn className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Log In to CampusOS
          </h1>
          <p className="text-xs text-slate-300">
            Access your Quai Campus Wallet, Marketplace, and Student Identity Card. 
          </p>
        </div>

        {/* Form Body */}
        <div className="p-8 space-y-6">
          {error && (
            <div
              className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-start gap-3"
              role="alert"
            >
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <strong className="font-bold">Login Error: </strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Institutional University Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="amina.bello@unn.edu.ng"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:bg-primary-300 text-white font-bold text-sm shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Logging in...</span>
                </>
              ) : (
                <>
                  <span>Log In to CampusOS</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Hackathon Judge & QA 1-Click Login Section */}
          <div className="border-t border-slate-200 pt-6 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
              <Sparkles className="h-4 w-4 text-amber-500" />
              <span>Hackathon Judge & QA: 1-Click Demo Logins</span>
            </div>
            <p className="text-xs text-slate-500">
              Instantly authenticate as any pre-seeded demo profile to explore roles and permissions:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDemoLogin("student-demo-001")}
                disabled={loading}
                className="px-3.5 py-2.5 rounded-xl border border-slate-300 hover:border-primary-500 bg-white hover:bg-slate-50 text-left text-xs font-semibold text-slate-700 transition-all flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-slate-900">Amina Bello</div>
                  <div className="text-[10px] text-slate-500">Student (Trust 50)</div>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                  Student
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin("student-wallet-01")}
                disabled={loading}
                className="px-3.5 py-2.5 rounded-xl border border-slate-300 hover:border-primary-500 bg-white hover:bg-slate-50 text-left text-xs font-semibold text-slate-700 transition-all flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-slate-900">Chidi Okafor</div>
                  <div className="text-[10px] text-slate-500">25.5 QUAI Faucet</div>
                </div>
                <span className="px-2 py-0.5 rounded bg-primary-50 text-primary-700 text-[10px] font-bold">
                  Wallet
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin("seller-01")}
                disabled={loading}
                className="px-3.5 py-2.5 rounded-xl border border-slate-300 hover:border-primary-500 bg-white hover:bg-slate-50 text-left text-xs font-semibold text-slate-700 transition-all flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-slate-900">Tunde Balogun</div>
                  <div className="text-[10px] text-slate-500">Verified Seller</div>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                  Verified
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin("admin-001")}
                disabled={loading}
                className="px-3.5 py-2.5 rounded-xl border border-amber-300 hover:border-amber-500 bg-amber-50/50 hover:bg-amber-50 text-left text-xs font-semibold text-slate-700 transition-all flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-slate-900">Dr. Nneka Eze</div>
                  <div className="text-[10px] text-slate-500">Admin Reviewer</div>
                </div>
                <span className="px-2 py-0.5 rounded bg-amber-500 text-white text-[10px] font-bold">
                  Admin
                </span>
              </button>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4 text-center text-xs text-slate-500">
            Don't have an account?{" "}
            <Link href="/signup" className="text-primary-600 font-bold hover:underline">
              Sign Up for CampusOS
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
