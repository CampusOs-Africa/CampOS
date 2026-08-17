"use client";

import React from "react";
import Link from "next/link";
import {
  QrCode,
  ShieldCheck,
  Download,
  RefreshCw,
  ExternalLink,
  Lock,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { CampusIdentityQR } from "../../components/identity/CampusIdentityQR";

export default function QrIdPage() {
  const { user, refreshUser, isLoading } = useAuth();

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
          Please log in to view or download your Campus Identity QR Card.
        </p>
        <Link
          href="/login"
          className="px-6 py-2.5 rounded-xl bg-primary-600 text-white font-bold text-sm inline-block"
        >
          Login
        </Link>
      </div>
    );
  }

  const handleDownloadQR = () => {
    // Find canvas in DOM and download as PNG
    const canvas = document.querySelector("canvas");
    if (canvas) {
      const url = canvas.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = url;
      a.download = `campusos-id-card-${user.name.replace(/\s+/g, "-").toLowerCase()}.png`;
      a.click();
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 text-white shadow-xl flex flex-col sm:flex-row items-center justify-between gap-6 border border-slate-700/50">
        <div className="space-y-2 text-center sm:text-left">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/40 text-primary-300 text-xs font-semibold">
            <QrCode className="h-4 w-4" />
            <span>Cryptographic Student ID Card</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Your Scannable Campus Identity QR Card
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
            Signed with HMAC-SHA256 cryptography. Campus merchants and administrators scan this card to verify your institutional enrollment without viewing sensitive PII.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => refreshUser(user.id)}
            className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/10 transition-all flex items-center gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh Card</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadQR}
            className="px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download PNG</span>
          </button>
        </div>
      </div>

      {/* QR Display Area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 flex flex-col items-center justify-center">
          <CampusIdentityQR userId={user.id} />
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <h3 className="font-bold text-slate-900">How QR Scanning Works</h3>
            </div>
            <ul className="space-y-2 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <span className="h-2 w-2 rounded-full bg-primary-600 mt-1 shrink-0" />
                <span>
                  <strong>Zero PII Exposure:</strong> Your admission letter and document photos are private. Vendors only see your verification badge and academic faculty.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-600 mt-1 shrink-0" />
                <span>
                  <strong>HMAC-SHA256 Signed:</strong> Every QR token is cryptographically signed by the backend. Altering any field invalidates the signature.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-600 mt-1 shrink-0" />
                <span>
                  <strong>Merchant Discounts:</strong> Show this card at campus bookstores and cafeterias to instantly receive verified student discounts.
                </span>
              </li>
            </ul>
          </div>

          <div className="bg-slate-900 text-white rounded-3xl p-6 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Status Verification Endpoint:</span>
              <span className="text-primary-400 font-mono">POST /api/v1/qr/verify</span>
            </div>
            <p className="text-xs text-slate-300">
              Administrators and merchants can click the <strong>"Scan QR Card"</strong> button in the top navigation bar to scan and verify cards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
