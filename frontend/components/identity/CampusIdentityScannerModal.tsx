"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import {
  QrCode,
  ShieldCheck,
  AlertCircle,
  Loader2,
  CheckCircle2,
  XCircle,
  Key,
  User,
  Calendar,
  ExternalLink,
} from "lucide-react";
import { VerificationBadge } from "../verification/VerificationBadge";

interface CampusIdentityScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  role?: "admin" | "merchant" | "student";
  apiBaseUrl?: string;
}

export const CampusIdentityScannerModal: React.FC<CampusIdentityScannerModalProps> = ({
  isOpen,
  onClose,
  role = "merchant",
  apiBaseUrl = API_BASE_URL,
}) => {
  const [rawPayload, setRawPayload] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!rawPayload.trim()) {
      setError("Please paste or scan a valid Campus Identity QR JSON payload.");
      return;
    }

    let parsedPayload: any;
    try {
      parsedPayload = JSON.parse(rawPayload);
    } catch (err) {
      setError("Malformed QR payload. Must be a valid JSON object encoded by CampusOS.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/verification/qr/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ payload: parsedPayload }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || data?.detail || "Cryptographic signature verification failed.");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to verify Campus Identity QR.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = () => {
    // Populate sample valid QR JSON payload for instant demo testing
    const sample = JSON.stringify(
      {
        user_id: "student-demo-001",
        status: "verified",
        credential_id: "0xquai_demo_credential_receipt_9000",
        timestamp: "2026-07-30T10:00:00Z",
        signature: "sample_hmac_sha256_signature_hex_digest_for_demo",
      },
      null,
      2
    );
    setRawPayload(sample);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
              <QrCode className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                {role === "admin" ? "Admin QR Identity Scanner" : "Merchant Campus ID Scanner"}
              </h3>
              <p className="text-xs text-slate-500">
                Cryptographically verify student UUID, status & digital signature.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleScan} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Scanned QR JSON Payload
              </label>
              <button
                type="button"
                onClick={handleLoadSample}
                className="text-xs text-primary-600 hover:text-primary-500 font-semibold"
              >
                + Load Demo Student QR
              </button>
            </div>
            <textarea
              rows={4}
              value={rawPayload}
              onChange={(e) => setRawPayload(e.target.value)}
              placeholder='Paste scanned QR JSON object (e.g. {"user_id": "...", "status": "verified", ...})'
              className="w-full rounded-xl border border-slate-300 p-3 text-xs font-mono text-slate-800 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          {error && (
            <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-800">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  <span className="text-sm font-bold text-emerald-900">
                    Valid Campus Identity — Signature Authentic
                  </span>
                </div>
                <VerificationBadge status={result.status} />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-emerald-800 pt-2 border-t border-emerald-200/60">
                <div>
                  <span className="text-emerald-600 font-medium block">Student UUID</span>
                  <span className="font-mono font-bold truncate block">{result.user_id}</span>
                </div>
                <div>
                  <span className="text-emerald-600 font-medium block">On-Chain Quai Status</span>
                  <span className="font-semibold uppercase block">{result.on_chain_status}</span>
                </div>
              </div>

              <div className="text-[11px] text-emerald-700 font-mono bg-emerald-100/60 p-2 rounded break-all">
                Cred ID: {result.credential_id}
              </div>

              <div className="text-[10px] text-emerald-600 flex items-center justify-between">
                <span>✓ Verified by: {result.verified_by}</span>
                <span>{new Date(result.timestamp).toLocaleDateString("en-NG")}</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setRawPayload("");
                setResult(null);
                setError(null);
              }}
              className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-xs font-semibold text-white shadow-sm transition-all disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Verifying Signature..." : "Verify Cryptographic Signature"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
