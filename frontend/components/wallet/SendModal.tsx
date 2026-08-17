"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { ArrowUpRight, Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";

interface SendModalProps {
  isOpen: boolean;
  onClose: () => void;
  senderId: string;
  balanceQuai: number;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const SendModal: React.FC<SendModalProps> = ({
  isOpen,
  onClose,
  senderId,
  balanceQuai,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txReceipt, setTxReceipt] = useState<any>(null);

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setTxReceipt(null);

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError("Please enter a valid transfer amount greater than 0.");
      return;
    }

    if (parsedAmount > balanceQuai) {
      setError(`Insufficient available balance. You currently have ${balanceQuai.toFixed(2)} QUAI.`);
      return;
    }

    if (!recipient.trim()) {
      setError("Please specify a recipient Quai EVM address, institutional email, or student UUID.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/wallet/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sender_id: senderId,
          recipient: recipient.trim(),
          amount_quai: parsedAmount,
          note: note.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || data?.detail || "Transfer failed.");
      }

      setTxReceipt(data);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || "Failed to complete QUAI transfer.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRecipient("");
    setAmount("");
    setNote("");
    setError(null);
    setTxReceipt(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
              <ArrowUpRight className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Send QUAI
              </h3>
              <p className="text-xs text-slate-500">
                Transfer Quai testnet tokens to any campus wallet or EVM address.
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

        {/* Success Receipt View */}
        {txReceipt ? (
          <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              <h4 className="text-base font-bold text-emerald-900">
                Transfer Confirmed on Quai!
              </h4>
            </div>
            <p className="text-xs text-emerald-800">
              {txReceipt.message}
            </p>
            <div className="p-3 rounded-lg bg-white border border-emerald-200 text-xs font-mono space-y-1">
              <div>
                <span className="text-slate-400">Recipient:</span>{" "}
                <span className="text-slate-900">{txReceipt.recipient}</span>
              </div>
              <div>
                <span className="text-slate-400">Amount:</span>{" "}
                <span className="text-emerald-700 font-bold">{txReceipt.amount_quai} QUAI</span>
              </div>
              <div>
                <span className="text-slate-400">Tx Hash:</span>{" "}
                <span className="text-slate-600 break-all">{txReceipt.tx_hash}</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all shadow-sm"
              >
                Send Another Transfer
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          /* Input Form */
          <form onSubmit={handleSend} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Recipient (Address, Institutional Email, or UUID)
              </label>
              <input
                type="text"
                required
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="0x... or amina.bello@unijos.edu.ng"
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                CampusOS automatically maps university emails to verified EVM addresses.
              </p>
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

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Payment Note / Memo (Optional)
              </label>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="e.g. Textbook split payment"
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none"
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
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Broadcasting..." : "Send QUAI Now"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
