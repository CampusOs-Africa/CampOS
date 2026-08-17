"use client";

import React from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ShieldCheck,
  ExternalLink,
  ShoppingBag,
  PackageCheck,
} from "lucide-react";

interface PurchaseConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: {
    id: string;
    payment_reference: string;
    escrow_tx_hash: string;
    amount: number;
    listing_title?: string;
  } | null;
}

export const PurchaseConfirmationModal: React.FC<PurchaseConfirmationModalProps> = ({
  isOpen,
  onClose,
  order,
}) => {
  if (!isOpen || !order) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="purchase-confirm-title"
    >
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Success Banner */}
        <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
          <div className="p-2.5 rounded-xl bg-emerald-100 text-emerald-600">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <div>
            <h3
              id="purchase-confirm-title"
              className="text-lg font-bold text-slate-900"
            >
              Order Confirmed & Quai Escrow Locked!
            </h3>
            <p className="text-xs text-slate-500">
              Blip Pay payment successful. Seller notified to fulfill delivery.
            </p>
          </div>
        </div>

        {/* Item Summary Box */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div>
            <span className="text-[11px] uppercase font-bold text-slate-400 block">
              Purchased Item
            </span>
            <h4 className="font-bold text-slate-900 text-sm mt-0.5">
              {order.listing_title || "Campus Marketplace Item"}
            </h4>
          </div>
          <div className="text-right">
            <span className="text-lg font-extrabold text-slate-900">
              ₦{order.amount.toLocaleString("en-NG")}
            </span>
            <span className="text-[10px] uppercase font-bold text-emerald-600 block">
              Paid via Blip Pay
            </span>
          </div>
        </div>

        {/* Escrow Details */}
        <div className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono space-y-2">
          <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
            <span className="flex items-center gap-1.5 font-sans font-semibold">
              <ShieldCheck className="h-4 w-4 text-emerald-400" /> Quai Escrow Contract Receipt
            </span>
            <span className="text-emerald-400 font-semibold">● LOCKED</span>
          </div>

          <div className="space-y-1">
            <div>
              <span className="text-slate-400">Order UUID: </span>
              <span className="text-slate-200 select-all">{order.id}</span>
            </div>
            <div>
              <span className="text-slate-400">Blip Ref: </span>
              <span className="text-slate-200 select-all">{order.payment_reference}</span>
            </div>
            <div>
              <span className="text-slate-400">Quai Escrow Tx: </span>
              <span className="text-emerald-300 break-all select-all block mt-0.5">
                {order.escrow_tx_hash}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2">
          <Link
            href={`https://testnet.quaiscan.io/tx/${order.escrow_tx_hash}`}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1 px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <span>Quai Explorer</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </Link>
          <Link
            href="/orders"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg transition-all"
          >
            <PackageCheck className="h-4 w-4" />
            <span>View in My Orders</span>
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-bold text-white transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
