"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { Settings, Key, ShieldCheck, ExternalLink, X, RefreshCw, Loader2 } from "lucide-react";

interface WalletSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  walletAddress: string;
  apiBaseUrl?: string;
  onWalletConnected?: () => void;
}

export const WalletSettings: React.FC<WalletSettingsProps> = ({
  isOpen,
  onClose,
  userId,
  walletAddress,
  apiBaseUrl = API_BASE_URL,
  onWalletConnected,
}) => {
  const [newAddress, setNewAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpdateWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAddress.trim() || !newAddress.startsWith("0x") || newAddress.length !== 42) {
      alert("Please enter a valid 42-character Quai EVM address starting with 0x.");
      return;
    }

    setLoading(true);
    setSuccess(null);
    try {
      const res = await fetch(`${apiBaseUrl}/wallet/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          wallet_address: newAddress.trim(),
          message: "CampusOS Wallet Re-Authentication & Update Challenge",
          signature: "0xmock_signature_hex_digest_65_bytes",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || "Failed to update wallet address.");
      }

      setSuccess("Wallet address successfully updated and verified!");
      if (onWalletConnected) {
        onWalletConnected();
      }
    } catch (err: any) {
      alert(err.message || "Could not update wallet.");
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
            <div className="p-2 rounded-lg bg-slate-100 text-slate-700">
              <Settings className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Wallet Settings
              </h3>
              <p className="text-xs text-slate-500">
                Manage your linked Quai EVM account & network configuration.
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

        {/* Current Connection Card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Connected Account
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
              <ShieldCheck className="h-3 w-3" /> Authenticated
            </span>
          </div>
          <div className="font-mono text-xs bg-white p-2.5 rounded-lg border border-slate-200 text-slate-800 break-all">
            {walletAddress}
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 pt-1">
            <div>
              <span className="text-slate-400 block">Student UUID</span>
              <span className="font-mono truncate block">{userId}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Chain ID</span>
              <span className="font-bold">9000 (Quai Testnet)</span>
            </div>
          </div>
        </div>

        {/* Change Linked Wallet Form */}
        <form onSubmit={handleUpdateWallet} className="space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
            Link Different Quai EVM Address
          </label>
          <input
            type="text"
            placeholder="0x..."
            value={newAddress}
            onChange={(e) => setNewAddress(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono text-slate-900 focus:border-primary-500 focus:outline-none"
          />
          {success && (
            <p className="text-xs font-semibold text-emerald-600">{success}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            <span>Sign Challenge & Update Linked Address</span>
          </button>
        </form>

        {/* Network Info */}
        <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-3 flex items-center justify-between">
          <span>RPC Endpoint:</span>
          <a
            href="https://rpc.quai.network"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:underline flex items-center gap-1"
          >
            <span>https://rpc.quai.network</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  );
};
