"use client";

import React from "react";
import {
  Wallet,
  ArrowUpRight,
  ArrowDownLeft,
  QrCode,
  PlusCircle,
  Download,
  Settings,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

interface BalanceCardProps {
  userId: string;
  walletAddress?: string | null;
  balanceQuai: number;
  balanceWei?: string;
  fiatValueNgn: number;
  network?: string;
  isVerified?: boolean;
  onSendClick: () => void;
  onReceiveClick: () => void;
  onDepositClick: () => void;
  onWithdrawClick: () => void;
  onSettingsClick: () => void;
  onRefresh: () => void;
}

export const BalanceCard: React.FC<BalanceCardProps> = ({
  userId,
  walletAddress = "0x0000000000000000000000000000000000000000",
  balanceQuai = 0,
  fiatValueNgn = 0,
  network = "Quai Network Testnet (Chain ID 9000)",
  isVerified = true,
  onSendClick,
  onReceiveClick,
  onDepositClick,
  onWithdrawClick,
  onSettingsClick,
  onRefresh,
}) => {
  const formattedAddress = walletAddress
    ? `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`
    : "Not Connected";

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl border border-slate-700/80 relative overflow-hidden">
      {/* Top row: Network badge & Settings */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-700/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary-500/20 border border-primary-500/40 text-primary-400">
            <Wallet className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary-400">
                {network}
              </span>
              {isVerified && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/40">
                  <ShieldCheck className="h-3 w-3" /> Verified Student
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="font-mono text-sm text-slate-300">{formattedAddress}</span>
              <button
                onClick={() => navigator.clipboard.writeText(walletAddress || "")}
                className="text-[11px] text-primary-400 hover:text-primary-300 underline"
                title="Copy Full Address"
              >
                Copy
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-slate-300 transition-colors border border-white/10"
            title="Refresh Balance"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={onSettingsClick}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold text-slate-200 transition-all border border-white/10"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Center row: Balance */}
      <div className="py-6 flex flex-col sm:flex-row sm:items-baseline justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Available Quai Balance
          </p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
              {balanceQuai.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
            </span>
            <span className="text-xl font-bold text-primary-400">QUAI</span>
          </div>
          <p className="mt-1 text-sm font-medium text-slate-400">
            ≈ ₦{fiatValueNgn.toLocaleString("en-NG", { minimumFractionDigits: 2 })} NGN
          </p>
        </div>

        <div className="text-right sm:text-right">
          <span className="text-xs text-slate-400 block">Student UUID:</span>
          <span className="font-mono text-xs text-slate-300">{userId}</span>
        </div>
      </div>

      {/* Bottom row: Action Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-700/80">
        <button
          onClick={onSendClick}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-sm font-bold text-white shadow-lg transition-all"
        >
          <ArrowUpRight className="h-4 w-4" />
          <span>Send QUAI</span>
        </button>

        <button
          onClick={onReceiveClick}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-700/80 hover:bg-slate-700 text-sm font-bold text-white border border-slate-600 transition-all"
        >
          <QrCode className="h-4 w-4 text-primary-400" />
          <span>QR Receive</span>
        </button>

        <button
          onClick={onDepositClick}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-sm font-bold text-emerald-300 border border-emerald-500/40 transition-all"
        >
          <PlusCircle className="h-4 w-4 text-emerald-400" />
          <span>Deposit</span>
        </button>

        <button
          onClick={onWithdrawClick}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-sm font-bold text-slate-300 border border-slate-700 transition-all"
        >
          <Download className="h-4 w-4 text-slate-400" />
          <span>Withdraw</span>
        </button>
      </div>
    </div>
  );
};
