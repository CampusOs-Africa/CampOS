"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ShoppingBag,
  Wallet,
  Lock,
  Award,
  ArrowRight,
  LayoutDashboard,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const { user, loginWithDemoUser } = useAuth();

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 sm:p-14 text-white shadow-xl relative overflow-hidden border border-slate-700/50">
        <div className="max-w-3xl space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/30 text-primary-400 text-xs font-semibold tracking-wide">
            <ShieldCheck className="h-4 w-4" />
            <span>Quai × Blip Buildathon Flagship — Campus Identity, Commerce & Trust</span>
          </div>

          <h1 className="text-3xl sm:text-6xl font-extrabold tracking-tight leading-tight">
            The Trusted Digital Operating System for African Universities
          </h1>

          <p className="text-slate-300 text-base sm:text-xl leading-relaxed max-w-2xl">
            Eliminate WhatsApp scams and anonymous campus vendors. CampusOS verifies institutional student identities via SHA-256 cryptographic hashes on <strong className="text-white">Quai Network</strong>, powers instant P2P payments with <strong className="text-white">Quai Campus Wallet</strong>, and protects commerce with <strong className="text-white">Blip Pay & Smart Escrow</strong>.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            {!user ? (
              <>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-7 py-3.5 text-sm font-bold text-white shadow-lg hover:bg-primary-500 transition-all transform hover:-translate-y-0.5"
                >
                  <span>Get Started</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-700/80 hover:bg-slate-700 px-7 py-3.5 text-sm font-semibold text-white transition-all border border-slate-600"
                >
                  <span>Login</span>
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-7 py-3.5 text-sm font-bold text-white shadow-lg hover:bg-primary-500 transition-all transform hover:-translate-y-0.5"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span>Go to Dashboard</span>
                </Link>
                <Link
                  href="/marketplace"
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-700/80 hover:bg-slate-700 px-6 py-3.5 text-sm font-semibold text-white transition-all border border-slate-600"
                >
                  <ShoppingBag className="h-4 w-4" />
                  <span>Browse Marketplace</span>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Hackathon 1-Click Interactive Demo Quick-Start */}
      {!user && (
        <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border border-amber-200 rounded-2xl p-6 shadow-sm">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Hackathon Judge & QA Demo Quick-Start
                </h3>
                <p className="text-xs text-slate-600">
                  Test the complete onboarding and escrow flow instantly without typing credentials:
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() =>
  loginWithDemoUser("e0d41398-e451-40ff-9b63-d8037f1dd71b")
}
                className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-300 hover:border-primary-500 text-xs font-semibold text-slate-700 hover:text-primary-600 shadow-sm transition-all flex items-center gap-1.5"
              >
                <span>Login as Amina (Student)</span>
                <span className="text-emerald-600 font-bold">50 pt</span>
              </button>
              <button
                type="button"
                onClick={() =>
  loginWithDemoUser("0e54ea5a-d4cc-4083-84b1-215eb35af3ab")
}
                className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-300 hover:border-primary-500 text-xs font-semibold text-slate-700 hover:text-primary-600 shadow-sm transition-all flex items-center gap-1.5"
              >
                <span>Login as Chidi (Wallet)</span>
                <span className="text-primary-600 font-bold">25 QUAI</span>
              </button>
              <button
                type="button"
                onClick={() =>
  loginWithDemoUser("eab2ec53-6553-4cee-88f9-7fbffa31fa03")
}
                className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow-sm transition-all flex items-center gap-1.5"
              >
                <span>Login as Admin</span>
                <span className="text-amber-400 font-bold">Reviewer</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4 Feature Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition-shadow">
          <div className="h-10 w-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <ShoppingBag className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-slate-900">100% Scam-Free Marketplace</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Only students with an approved Verified Student Identity can create listings. All orders are locked in Quai Network smart contract escrow until delivery is confirmed.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition-shadow">
          <div className="h-10 w-10 rounded-xl bg-primary-50 flex items-center justify-center text-primary-600">
            <Wallet className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-slate-900">Quai Campus Wallet</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Connect your Quai EVM wallet via off-chain signature challenge. Send, receive, deposit, and withdraw QUAI testnet tokens instantly with live Naira equivalent.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition-shadow">
          <div className="h-10 w-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Lock className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-slate-900">Off-Chain PII Protection</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Student ID cards and admission letters are never stored in PostgreSQL or exposed on-chain. Secure URLs are stored in Cloudinary with strict file validation.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition-shadow">
          <div className="h-10 w-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
            <Award className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-slate-900">Automated Trust Rewards</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Earn +10 for identity verification, +5 for completing orders as buyer or seller, and +2 for receiving positive peer reviews. Bounded 0–100.
          </p>
        </div>
      </div>

      {/* About Section */}
      <div id="about" className="bg-white rounded-3xl p-8 sm:p-12 border border-slate-200 shadow-sm space-y-8">
        <div className="max-w-2xl space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            How CampusOS Solves African Campus Commerce
          </h2>
          <p className="text-slate-600 text-sm sm:text-base">
            Designed for Nigerian and African university ecosystems where peer-to-peer commerce is vibrant but often hindered by trust deficits.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-base">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <span>1. Verified Institutional Identity</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              Every student registers with their university email (.edu.ng) and uploads admission letter proof. Administrators approve KYC with one click.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-base">
              <CheckCircle2 className="h-5 w-5 text-primary-600" />
              <span>2. Quai Network Hash Anchor</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              When approved, only a 32-byte SHA-256 digest is stored on-chain in <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">StudentIdentity.sol</code>. Zero PII ever touches the blockchain.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900 text-base">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <span>3. Smart Contract Escrow</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              Buyers lock funds in <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">MarketplaceEscrow.sol</code>. Sellers ship with confidence, knowing payment is guaranteed upon delivery.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
