"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { Download, Loader2, CheckCircle2, AlertCircle, X, ArrowRight } from "lucide-react";

interface WithdrawModalProps {
  isOpen: boolean;
  onClose: () => void;
  senderId: string;
  balanceQuai: number;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const WithdrawModal: React.FC<WithdrawModalProps> = ({
  isOpen,
  onClose,
  senderId,
  balanceQuai,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [destination, setDestination] = useState("");
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txReceipt, setTxReceipt] = useState<any>(null);

  if (!isOpen) return null;

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setTxReceipt(null);

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError("Please enter a valid withdrawal amount greater than 0.");
      return;
    }

    if (parsedAmount > balanceQuai) {
      setError(`Insufficient available balance. You currently have ${balanceQuai.toFixed(2)} QUAI.`);
      return;
    }

    if (!destination.trim() || !destination.startsWith("0x")) {
      setError("Please enter a valid external Quai EVM address (0x...) for withdrawal.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/wallet/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_id: senderId,
          recipient: destination.trim(),
          amount_quai: parsedAmount,
          note: "CampusOS Wallet Withdrawal to External EVM Address",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || "Withdrawal failed.");
      }

      setTxReceipt(data);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || "Failed to withdraw QUAI tokens.");
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
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <Download className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Withdraw QUAI
              </h3>
              <p className="text-xs text-slate-500">
                Transfer tokens to an external EVM wallet or fiat bridge.
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

        {txReceipt ? (
          <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              <h4 className="text-base font-bold text-emerald-900">
                Withdrawal Confirmed!
              </h4>
            </div>
            <p className="text-xs text-emerald-800">
              {txReceipt.message}
            </p>
            <div className="p-3 rounded-lg bg-white border border-emerald-200 text-xs font-mono break-all">
              Tx Hash: {txReceipt.tx_hash}
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleWithdraw} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Destination External EVM Address (0x...)
              </label>
              <input
                type="text"
                required
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="0x..."
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm font-mono text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Amount in QUAI
                </label>
                <span className="text-xs text-slate-500 font-medium">
                  Available: <strong className="text-slate-900">{balanceQuai.toFixed(2)} QUAI</strong>
                </span>
              </div>
              <input
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm font-bold text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2 text-xs text-red-800">
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Withdrawing..." : "Withdraw QUAI"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
