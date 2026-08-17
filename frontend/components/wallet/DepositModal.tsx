"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { PlusCircle, ExternalLink, Loader2, CheckCircle2, QrCode, X } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

interface DepositModalProps {
  isOpen: boolean;
  onClose: () => void;
  walletAddress: string;
  userId: string;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const DepositModal: React.FC<DepositModalProps> = ({
  isOpen,
  onClose,
  walletAddress,
  userId,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleClaimFaucet = async () => {
    setLoading(true);
    setSuccessMsg(null);
    try {
      // Create a testnet faucet deposit transaction via wallet connect or simulated send
      const res = await fetch(`${apiBaseUrl}/wallet/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_id: userId,
          recipient: walletAddress,
          amount_quai: 25.0,
          note: "CampusOS Testnet Faucet Claim (+25.0 QUAI)",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || "Faucet claim failed.");
      }

      setSuccessMsg("Successfully deposited 25.0 QUAI from the Quai Testnet Faucet into your Campus Wallet!");
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      alert(err.message || "Could not claim faucet tokens.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <PlusCircle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Deposit QUAI
              </h3>
              <p className="text-xs text-slate-500">
                Fund your Campus Wallet with Quai Network testnet tokens.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            <p className="text-xs text-emerald-800 font-semibold">{successMsg}</p>
          </div>
        )}

        {/* Faucet Box */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900">
              1. Quai Testnet Faucet
            </h4>
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">
              Instant Demo
            </span>
          </div>
          <p className="text-xs text-slate-600">
            For Quai × Blip Buildathon judges and students testing the platform, claim 25.0 QUAI testnet tokens instantly.
          </p>
          <button
            onClick={handleClaimFaucet}
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Depositing Faucet Tokens..." : "Claim 25.0 QUAI Testnet Faucet"}
          </button>
        </div>

        {/* External Deposit info */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3">
          <h4 className="text-sm font-bold text-slate-900">
            2. Deposit from EVM Wallet / Exchange
          </h4>
          <p className="text-xs text-slate-600">
            Send QUAI from Pelagus, MetaMask, or the official Quai Testnet Faucet to your checksum address:
          </p>
          <div className="font-mono text-xs bg-slate-100 p-2.5 rounded-lg text-slate-800 break-all select-all">
            {walletAddress}
          </div>
          <a
            href="https://faucet.quai.network"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary-600 hover:underline font-semibold"
          >
            <span>Open Official Quai Network Faucet</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
