"use client";

import React, { useState } from "react";
import {
  ArrowUpRight,
  ArrowDownLeft,
  PlusCircle,
  Download,
  ExternalLink,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
} from "lucide-react";

export interface TransactionItem {
  id: string;
  user_id: string;
  wallet_address: string;
  recipient_address: string;
  amount: number;
  tx_hash: string;
  type: string; // 'send', 'receive', 'deposit', 'withdraw', 'faucet'
  status: string; // 'confirmed', 'pending', 'failed'
  network?: string;
  block_number?: number | null;
  note?: string | null;
  created_at: string;
}

interface TransactionListProps {
  transactions: TransactionItem[];
  loading?: boolean;
}

export const TransactionList: React.FC<TransactionListProps> = ({
  transactions = [],
  loading = false,
}) => {
  const [filter, setFilter] = useState<string>("all");

  const filteredTxs = transactions.filter((tx) => {
    if (filter === "all") return true;
    return tx.type.toLowerCase() === filter.toLowerCase();
  });

  const getTxIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "send":
        return <ArrowUpRight className="h-5 w-5 text-red-500" />;
      case "receive":
        return <ArrowDownLeft className="h-5 w-5 text-emerald-600" />;
      case "faucet":
      case "deposit":
        return <PlusCircle className="h-5 w-5 text-emerald-600" />;
      case "withdraw":
        return <Download className="h-5 w-5 text-amber-600" />;
      default:
        return <FileText className="h-5 w-5 text-slate-500" />;
    }
  };

  const getTxBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Confirmed
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-200">
            <Clock className="h-3 w-3 animate-spin text-amber-500" /> Pending
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 border border-red-200">
            <AlertCircle className="h-3 w-3 text-red-500" /> Failed
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header & Filter Bar */}
      <div className="p-6 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">
            Quai Transaction History
          </h3>
          <p className="text-sm text-slate-500">
            Immutable on-chain ledger of your P2P sends, receives, and testnet faucet claims.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {["all", "send", "receive", "faucet", "deposit", "withdraw"].map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                filter === t
                  ? "bg-slate-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Transaction Feed */}
      <div className="divide-y divide-slate-100">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary-600 mb-2" />
            Loading transaction history...
          </div>
        ) : filteredTxs.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-500 italic">
            No transactions found matching filter '{filter}'.
          </div>
        ) : (
          filteredTxs.map((tx) => {
            const isIncoming = tx.type === "receive" || tx.type === "faucet" || tx.type === "deposit";
            const formattedDate = new Date(tx.created_at).toLocaleString("en-NG", {
              dateStyle: "short",
              timeStyle: "short",
            });
            const counterparty = isIncoming ? tx.wallet_address : tx.recipient_address;
            const shortCounterparty = `${counterparty.slice(0, 6)}...${counterparty.slice(-4)}`;

            return (
              <div
                key={tx.id}
                className="p-4 sm:p-5 hover:bg-slate-50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-slate-100 mt-0.5">
                    {getTxIcon(tx.type)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900 capitalize">
                        {tx.type === "faucet" ? "Testnet Welcome Faucet" : `${tx.type} QUAI`}
                      </span>
                      {getTxBadge(tx.status)}
                    </div>
                    {tx.note && (
                      <p className="text-xs text-slate-600 mt-0.5">{tx.note}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                      <span>{isIncoming ? "From:" : "To:"}</span>
                      <span className="font-mono text-slate-600">{shortCounterparty}</span>
                      <span>●</span>
                      <span>{formattedDate}</span>
                    </div>
                  </div>
                </div>

                <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center">
                  <span
                    className={`text-base font-extrabold font-mono ${
                      isIncoming ? "text-emerald-600" : "text-slate-900"
                    }`}
                  >
                    {isIncoming ? "+" : "-"}{tx.amount.toFixed(2)} QUAI
                  </span>
                  <a
                    href={`https://testnet.quaiscan.io/tx/${tx.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-600 hover:underline mt-0.5"
                    title="View on Quai Testnet Explorer"
                  >
                    <span>Quai Receipt</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
