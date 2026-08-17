"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
  AlertCircle,
  RefreshCw,
  Copy,
  Check,
  QrCode,
  ShieldCheck,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { VerificationBadge } from "./VerificationBadge";

interface BlockchainStatusData {
  user_id: string;
  is_verified: boolean;
  credential_hash?: string | null;
  status: string;
  tx_hash?: string | null;
  timestamp?: string;
}

interface BlockchainStatusMonitorProps {
  userId: string;
  initialTxHash?: string | null;
  credentialHash?: string | null;
  apiBaseUrl?: string;
  pollingIntervalMs?: number;
}

export const BlockchainStatusMonitor: React.FC<BlockchainStatusMonitorProps> = ({
  userId,
  initialTxHash,
  credentialHash,
  apiBaseUrl = API_BASE_URL,
  pollingIntervalMs = 4000,
}) => {
  const [data, setData] = useState<BlockchainStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const fetchBlockchainStatus = useCallback(async (isRetry = false) => {
    if (isRetry) {
      setRetrying(true);
      setError(null);
    }
    try {
      const res = await fetch(`${apiBaseUrl}/verification/blockchain/${userId}`);
      if (!res.ok) {
        throw new Error("Failed to fetch live Quai blockchain verification status.");
      }
      const json: BlockchainStatusData = await res.json();
      setData(json);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Error connecting to Quai Network RPC node.");
    } finally {
      setLoading(false);
      if (isRetry) {
        setRetrying(false);
      }
    }
  }, [apiBaseUrl, userId]);

  useEffect(() => {
    fetchBlockchainStatus();

    // Stop polling automatically as soon as verified or approved, or when tab is hidden
    if (
      data?.is_verified === true ||
      data?.status === "verified" ||
      data?.status === "approved" ||
      (typeof document !== "undefined" && document.hidden)
    ) {
      return;
    }

    const interval = setInterval(() => {
      if (typeof document !== "undefined" && document.hidden) {
        return;
      }
      fetchBlockchainStatus();
    }, pollingIntervalMs);

    return () => clearInterval(interval);
  }, [fetchBlockchainStatus, pollingIntervalMs, data?.is_verified, data?.status]);

  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentTxHash = data?.tx_hash || initialTxHash;
  const currentCredHash = data?.credential_hash || credentialHash;
  const isConfirmed = data?.is_verified === true && currentTxHash && currentTxHash !== "on-chain-query";
  const isPending = !isConfirmed && loading;
  const explorerUrl = currentTxHash
    ? `https://testnet.quaiscan.io/tx/${currentTxHash}`
    : "https://testnet.quaiscan.io";

  // 1. Loading Skeleton View
  if (loading && !data && !error) {
    return (
      <div className="mt-6 p-6 rounded-xl border border-slate-200 bg-slate-50 space-y-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 bg-slate-300 rounded"></div>
          <div className="h-6 w-24 bg-slate-300 rounded-full"></div>
        </div>
        <div className="h-4 w-3/4 bg-slate-200 rounded"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="h-24 bg-slate-200 rounded-lg"></div>
          <div className="h-24 bg-slate-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 p-6 sm:p-8 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-lg space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-700">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            <h3 className="text-lg font-bold tracking-tight">
              Live Quai Network Blockchain Verification
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time on-chain credential monitor powered by Quai EVM Testnet (Chain ID: 9000).
          </p>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {isConfirmed ? (
            <>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Verification Complete
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/40 text-primary-300 text-xs font-semibold">
                Transaction Confirmed
              </span>
            </>
          ) : (
            <>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-semibold">
                <Clock className="h-3.5 w-3.5 animate-spin text-amber-400" />
                Blockchain Pending
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-500/40 text-blue-300 text-xs font-semibold">
                Transaction Submitted
              </span>
            </>
          )}
          <VerificationBadge status={data?.status || "verified"} />
        </div>
      </div>

      {/* Error & Retry State */}
      {error && (
        <div className="p-4 rounded-lg bg-red-900/40 border border-red-500/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-200">
                Connection to Quai RPC Interrupted
              </p>
              <p className="text-xs text-red-300 mt-0.5">{error}</p>
            </div>
          </div>
          <button
            onClick={() => fetchBlockchainStatus(true)}
            disabled={retrying}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-semibold text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? "Retrying..." : "Retry Connection"}
          </button>
        </div>
      )}

      {/* Blockchain Data & QR Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        {/* Left 2 cols: Hash & Explorer info */}
        <div className="lg:col-span-2 space-y-4">
          {/* Transaction Hash Box */}
          <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Transaction Hash (Quai EVM Receipt)</span>
              {currentTxHash && (
                <button
                  onClick={() => handleCopyHash(currentTxHash)}
                  className="inline-flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied!" : "Copy Hash"}
                </button>
              )}
            </div>
            <div className="font-mono text-xs text-emerald-300 break-all select-all">
              {currentTxHash || "0xquai_pending_confirmation_..."}
            </div>
          </div>

          {/* Credential Hash Box */}
          {currentCredHash && (
            <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 space-y-1.5">
              <div className="text-xs text-slate-400">
                SHA-256 Credential Hash (Stored on StudentIdentity Contract)
              </div>
              <div className="font-mono text-xs text-slate-200 break-all select-all">
                {currentCredHash}
              </div>
            </div>
          )}

          {/* Explorer Button */}
          <div className="flex items-center gap-4 pt-2">
            <a
              href={explorerUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-primary-500 transition-all"
            >
              <span>View on Quai Testnet Explorer</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>

            <span className="text-xs text-slate-400">
              ● Live Polling Active ({pollingIntervalMs / 1000}s)
            </span>
          </div>
        </div>

        {/* Right col: Scannable Verification QR Code */}
        <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white text-slate-900 border border-slate-200 text-center space-y-2">
          <div className="p-2 bg-white rounded-lg border border-slate-100 shadow-sm">
            <QRCodeSVG
              value={`campusos:verify:${userId}:${currentCredHash || currentTxHash || "verified"}`}
              size={130}
              level="H"
              includeMargin={false}
            />
          </div>
          <div className="space-y-0.5">
            <p className="text-xs font-bold text-slate-900 flex items-center justify-center gap-1">
              <QrCode className="h-3.5 w-3.5 text-primary-600" /> Verification QR
            </p>
            <p className="text-[11px] text-slate-500">
              Scan for CampusOS On-Chain Proof
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
