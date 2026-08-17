"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ShieldCheck,
  ShieldAlert,
  Wallet,
  ShoppingBag,
  PackageCheck,
  QrCode,
  Award,
  ArrowRight,
  Sparkles,
  User,
  Bell,
  CheckCircle2,
  Clock,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { TrustScoreGauge } from "../../components/trust/TrustScoreGauge";

export default function DashboardPage() {
  const router = useRouter();
  const { user, refreshUser, isLoading } = useAuth();
  const [walletBalance, setWalletBalance] = useState<{
    balance_quai: number;
    fiat_value_ngn: number;
  } | null>(null);

  useEffect(() => {
    if (user?.id) {
      refreshUser(user.id);
      fetch(`${API_BASE_URL}/wallet/balance?user_id=${user.id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((json) => {
          if (json) {
            setWalletBalance({
              balance_quai: json.balance_quai || 25.5,
              fiat_value_ngn: json.fiat_value_ngn || 38250.0,
            });
          }
        })
        .catch(() => {});
    }
  }, [user?.id, refreshUser]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-800">Authentication Required</h2>
        <p className="text-sm text-slate-600">
          Please log in or register to view your CampusOS dashboard.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/login"
            className="px-6 py-2.5 rounded-xl bg-primary-600 text-white font-bold text-sm"
          >
            Login
          </Link>
          <Link
            href="/signup"
            className="px-6 py-2.5 rounded-xl bg-slate-200 text-slate-800 font-bold text-sm"
          >
            Sign Up
          </Link>
        </div>
      </div>
    );
  }

  const isAdmin = user.role === "admin";
  const isVerified =
    user.verification_status === "approved" ||
    user.verification_status === "verified";

  return (
    <div className="space-y-10">
      {/* Top Welcome Header Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 sm:p-12 text-white shadow-xl relative overflow-hidden border border-slate-700/50">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/40 text-primary-300 text-xs font-semibold">
              <LayoutDashboard className="h-3.5 w-3.5" />
              <span>Student Operating Center</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Welcome back, {user.name}
            </h1>
            <p className="text-slate-300 text-xs sm:text-sm">
              {user.school} • {user.faculty} • {user.department}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div
              className={`px-4 py-2 rounded-xl border text-xs font-bold flex items-center gap-2 ${
                isVerified
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                  : "bg-amber-500/20 text-amber-300 border-amber-500/40"
              }`}
            >
              {isAdmin ? (
                <>
                  <ShieldAlert className="h-4 w-4" />
                  <span>Administrator (Full Access)</span>
                </>
              ) : isVerified ? (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  <span>Verified Student (On-Chain SHA-256)</span>
                </>
              ) : (
                <>
                  <Clock className="h-4 w-4" />
                  <span>Verification Status: {user.verification_status || "Pending"}</span>
                </>
              )}
            </div>

            <Link
              href="/profile"
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs border border-white/10 transition-all flex items-center gap-1.5"
            >
              <User className="h-3.5 w-3.5" />
              <span>Edit Profile</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Actionable Onboarding Banner if Not Approved Yet */}
      {!isVerified && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-amber-900">
            <ShieldAlert className="h-8 w-8 text-amber-600 shrink-0" />
            <div>
              <h3 className="font-bold text-sm">
                Your Student Verification is Pending (+10 Trust Score Available)
              </h3>
              <p className="text-xs text-amber-800">
                Verify your institutional student ID or check your administrative approval status to unlock selling on the Campus Marketplace.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/upload-id"
              className="px-4 py-2 rounded-xl bg-white border border-amber-300 hover:bg-amber-100 text-amber-900 font-bold text-xs transition-colors"
            >
              Upload Student ID
            </Link>
            <Link
              href="/approval"
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold text-xs shadow-sm transition-colors flex items-center gap-1"
            >
              <span>Check Status</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* 4 Feature Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Wallet Balance Card */}
        <Link
          href="/wallet"
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-primary-300 transition-all group flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold">
              <Wallet className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-slate-400 group-hover:text-primary-600 flex items-center">
              Open Wallet <ChevronRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Quai Campus Wallet
            </div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1">
              {walletBalance ? `${walletBalance.balance_quai} QUAI` : "25.5 QUAI"}
            </div>
            <div className="text-xs text-emerald-600 font-bold mt-0.5">
              ≈ ₦{walletBalance ? walletBalance.fiat_value_ngn.toLocaleString() : "38,250"} NGN
            </div>
          </div>
        </Link>

        {/* Marketplace Shortcut */}
        <Link
          href="/marketplace"
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all group flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <ShoppingBag className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-slate-400 group-hover:text-emerald-600 flex items-center">
              Browse <ChevronRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Campus Marketplace
            </div>
            <div className="text-xl font-extrabold text-slate-900 mt-1">
              {isVerified ? "Buy & Sell Active" : "Buyer Access"}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Textbooks, laptops & hostel leases
            </div>
          </div>
        </Link>

        {/* Escrow & Orders Shortcut */}
        <Link
          href="/orders"
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-primary-300 transition-all group flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold">
              <PackageCheck className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-slate-400 group-hover:text-primary-600 flex items-center">
              My Orders <ChevronRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Smart Escrow & Orders
            </div>
            <div className="text-xl font-extrabold text-slate-900 mt-1">
              Quai CEI Protected
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              100% Guaranteed P2P Settlement
            </div>
          </div>
        </Link>

        {/* QR Student ID Card Shortcut */}
        <Link
          href="/qr"
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-primary-300 transition-all group flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-10 w-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
              <QrCode className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold text-slate-400 group-hover:text-purple-600 flex items-center">
              View Card <ChevronRight className="h-3.5 w-3.5" />
            </span>
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Campus Identity QR
            </div>
            <div className="text-xl font-extrabold text-slate-900 mt-1">
              HMAC-SHA256 Signed
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Scannable ID & Vendor Discounts
            </div>
          </div>
        </Link>
      </div>

      {/* Trust Score & Verification Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-500" />
              <h2 className="font-bold text-lg text-slate-900">
                Your Campus Trust Reputation Score (Milestone 6)
              </h2>
            </div>
            <Link
              href="/trust"
              className="text-xs font-bold text-primary-600 hover:underline flex items-center gap-1"
            >
              <span>Full Analytics</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
            <TrustScoreGauge
              data={{
                user_id: user.id,
                name: user.name,
                email: user.email,
                verification_status: user.verification_status || "pending",
                trust_score: user.trust_score || 50,
                trust_badge:
                  (user.trust_score || 50) >= 85
                    ? "Platinum"
                    : (user.trust_score || 50) >= 70
                    ? "Gold"
                    : (user.trust_score || 50) >= 55
                    ? "Silver"
                    : "Bronze",
                total_positive_earned: 10,
                total_penalties_deducted: 0,
                completed_sales: 1,
                peer_reviews_count: 2,
                average_rating: 4.8,
              }}
            />

            <div className="space-y-3 text-sm max-w-sm">
              <div className="font-bold text-slate-900">
                Reputation Tiers & Scoring Rules:
              </div>
              <ul className="space-y-1.5 text-xs text-slate-600">
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span><strong>+10 points:</strong> Approved Student Verification (KYC)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-primary-500" />
                  <span><strong>+5 points:</strong> Order release (Buyer & Seller)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-purple-500" />
                  <span><strong>+5 points:</strong> Wallet P2P token transfer</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-amber-500" />
                  <span><strong>+2 points:</strong> Positive Marketplace order review</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Quick Links & Notifications Card */}
        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-4">
            <Bell className="h-5 w-5 text-primary-600" />
            <h3 className="font-bold text-lg text-slate-900">
              Activity & Notifications
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="font-bold text-slate-900 flex items-center justify-between">
                <span>Account Created</span>
                <span className="text-slate-400">Today</span>
              </div>
              <p className="text-slate-600">
                You received a starting baseline Trust Score of 50.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-primary-50/60 border border-primary-100 space-y-1">
              <div className="font-bold text-primary-900 flex items-center justify-between">
                <span>Quai Testnet Faucet</span>
                <span className="text-primary-600 font-bold">+25 QUAI</span>
              </div>
              <p className="text-primary-800">
                Onboarding welcome deposit credited to your campus wallet.
              </p>
            </div>

            {isVerified && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1">
                <div className="font-bold text-emerald-900 flex items-center justify-between">
                  <span>Student KYC Approved</span>
                  <span className="text-emerald-600 font-bold">+10 pt</span>
                </div>
                <p className="text-emerald-800">
                  Your SHA-256 hash is anchored on Quai Network. Seller access unlocked!
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
