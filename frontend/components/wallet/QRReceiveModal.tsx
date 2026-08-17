"use client";

import React, { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { QrCode, Copy, Check, X, ShieldCheck } from "lucide-react";

interface QRReceiveModalProps {
  isOpen: boolean;
  onClose: () => void;
  walletAddress: string;
  userName?: string;
  isVerified?: boolean;
}

export const QRReceiveModal: React.FC<QRReceiveModalProps> = ({
  isOpen,
  onClose,
  walletAddress,
  userName = "Student Wallet",
  isVerified = true,
}) => {
  const [copied, setCopied] = useState(false);
  const [requestAmount, setRequestAmount] = useState<string>("");

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(walletAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const qrPayload = requestAmount
    ? `ethereum:${walletAddress}?value=${requestAmount}`
    : `ethereum:${walletAddress}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
              <QrCode className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Receive QUAI
              </h3>
              <p className="text-xs text-slate-500">
                Scan QR or copy address to deposit Quai Testnet tokens.
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

        {/* User identification badge */}
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-700">{userName}</span>
          {isVerified && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-700 border border-emerald-200">
              <ShieldCheck className="h-3 w-3 text-emerald-600" /> Verified Quai Address
            </span>
          )}
        </div>

        {/* QR Code Graphic */}
        <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-slate-50 border border-slate-200 shadow-inner">
          <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
            <QRCodeSVG value={qrPayload} size={180} level="H" includeMargin={false} />
          </div>
          <p className="mt-3 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            Quai EVM Testnet (Chain ID 9000)
          </p>
        </div>

        {/* Address & Copy Button */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
            Your Public Receive Address
          </label>
          <div className="flex items-center gap-2">
            <div className="flex-1 font-mono text-xs bg-slate-100 border border-slate-200 rounded-lg p-3 text-slate-800 break-all select-all">
              {walletAddress}
            </div>
            <button
              onClick={handleCopy}
              className="px-4 py-3 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-semibold text-xs transition-all shadow-sm shrink-0 flex items-center gap-1"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-300" /> : <Copy className="h-4 w-4" />}
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>

        {/* Optional Amount Request */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Request Specific Amount (Optional)
          </label>
          <input
            type="number"
            step="0.01"
            placeholder="e.g. 5.0 QUAI"
            value={requestAmount}
            onChange={(e) => setRequestAmount(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
          />
        </div>

        {/* Footer info */}
        <div className="text-[11px] text-slate-400 text-center border-t border-slate-100 pt-3">
          Only send QUAI or native Quai Network testnet tokens to this address.
        </div>
      </div>
    </div>
  );
};
