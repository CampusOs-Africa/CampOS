"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { ShieldCheck, CheckCircle2, AlertTriangle, Loader2, ArrowRight } from "lucide-react";

interface EscrowActionsProps {
  orderId: string;
  orderStatus: string;
  actorId: string;
  apiBaseUrl?: string;
  onActionComplete?: () => void;
}

export const EscrowActions: React.FC<EscrowActionsProps> = ({
  orderId,
  orderStatus,
  actorId,
  apiBaseUrl = API_BASE_URL,
  onActionComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [actionType, setActionType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleAction = async (endpoint: string, successMessage: string) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    setActionType(endpoint);

    try {
      const res = await fetch(`${apiBaseUrl}/orders/${orderId}/${endpoint}?actor_id=${actorId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: endpoint === "dispute" ? "Buyer reported delivery discrepancy" : undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || "Escrow action failed.");
      }

      setSuccess(successMessage);
      if (onActionComplete) {
        onActionComplete();
      }
    } catch (err: any) {
      setError(err.message || "Failed to execute escrow action.");
    } finally {
      setLoading(false);
      setActionType(null);
    }
  };

  if (orderStatus === "completed") {
    return (
      <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          <span className="text-sm font-bold text-emerald-900">
            Escrow Released — Order Completed
          </span>
        </div>
        <span className="text-xs font-semibold text-emerald-700">
          +5 Trust Score Awarded to Buyer & Seller
        </span>
      </div>
    );
  }

  if (orderStatus === "disputed") {
    return (
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <span className="text-sm font-bold text-amber-900">
            Order Disputed — Under Admin Governance Review
          </span>
        </div>
        <span className="text-xs font-semibold text-amber-700">
          Funds locked in Quai MarketplaceEscrow contract
        </span>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Escrow Lifecycle Actions (Order Status: {orderStatus})
        </span>
        <span className="text-xs text-primary-600 font-semibold flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5" /> Quai Network Protected
        </span>
      </div>

      {error && (
        <p className="text-xs font-semibold text-red-600">{error}</p>
      )}
      {success && (
        <p className="text-xs font-semibold text-emerald-600">{success}</p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {(orderStatus === "escrow_locked" || orderStatus === "escrow_funded") && (
          <button
            onClick={() => handleAction("confirm-shipment", "Shipment confirmed. Order marked in transit.")}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 disabled:opacity-50"
          >
            {loading && actionType === "confirm-shipment" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            <span>Confirm Shipment</span>
          </button>
        )}

        {(orderStatus === "escrow_locked" || orderStatus === "escrow_funded" || orderStatus === "shipped_pending_delivery") && (
          <button
            onClick={() => handleAction("confirm-delivery", "Delivery confirmed. Awaiting final escrow release.")}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 disabled:opacity-50"
          >
            {loading && actionType === "confirm-delivery" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            <span>Confirm Item Delivery</span>
          </button>
        )}

        {(orderStatus === "escrow_locked" || orderStatus === "escrow_funded" || orderStatus === "shipped_pending_delivery" || orderStatus === "delivered_pending_release") && (
          <>
            <button
              onClick={() => handleAction("release-escrow", "Escrow released! +5 Trust Score awarded to Buyer and Seller.")}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              {loading && actionType === "release-escrow" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Release Quai Escrow (+5 Trust Score)</span>
            </button>

            <button
              onClick={() => handleAction("dispute", "Order disputed. Submitted to admin governance review.")}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              {loading && actionType === "dispute" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Dispute Order</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};
