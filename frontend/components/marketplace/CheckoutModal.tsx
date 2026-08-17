"use client";

import { API_BASE_URL } from "../../lib/api";
import * as blip from "../../lib/blip";

import React, { useState } from "react";
import {
  ShieldCheck,
  Lock,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  CreditCard,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { MarketplaceListingItem } from "./ListingCard";
import { PurchaseConfirmationModal } from "./PurchaseConfirmationModal";

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  listing: MarketplaceListingItem | null;
  buyerId: string;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

function depositData(orderIdHex: string): string {
  // deposit(bytes32) selector = 0xb214faa5
  const hex = orderIdHex.startsWith("0x") ? orderIdHex.slice(2) : orderIdHex;
  return "0xb214faa5" + hex.padStart(64, "0");
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  isOpen,
  onClose,
  listing,
  buyerId,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderResult, setOrderResult] = useState<any>(null);
  const [status, setStatus] = useState<string>("");

  if (!isOpen || !listing) return null;

  const pollStatus = async (intentId: string, token: string) => {
    // Payment success can only come from a verified provider webhook. We poll
    // the server's authoritative status; a browser redirect never proves pay.
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      try {
        const r = await fetch(`${apiBaseUrl}/payments/intent/${intentId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!r.ok) continue;
        const s = await r.json();
        setStatus(s.status);
        if (["paid", "failed", "cancelled", "expired", "refunded"].includes(s.status)) {
          if (s.status === "paid" && onSuccess) onSuccess();
          return s.status;
        }
      } catch {
        // keep polling on transient errors
      }
    }
    return "pending";
  };

  const handleCheckout = async () => {
    setLoading(true);
    setError(null);
    setOrderResult(null);
    setStatus("creating");

    try {
      const token = localStorage.getItem("campusos_auth_token") || "";
      const initRes = await fetch(`${apiBaseUrl}/payments/intent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ listing_id: listing.id }),
      });
      const intent = await initRes.json();
      if (!initRes.ok) {
        throw new Error(intent?.detail || intent?.error?.message || "Checkout failed.");
      }
      setStatus("pending");

      // Blip self-custody Quai wallet flow. The backend independently
      // verifies the resulting transaction; the hash alone is not proof.
      const provider = blip.detectBlip();
      if (!provider) {
        throw new Error(
          "Blip wallet not detected. Please open this page in the Blip in-app browser."
        );
      }
      setStatus("connecting");
      await blip.connectBlip(provider);
      await blip.ensureOrchard(provider);

      const escrowAddress =
        process.env.NEXT_PUBLIC_CAMPUS_ESCROW_ADDRESS || "";
      if (!escrowAddress) {
        throw new Error("Escrow contract is not configured.");
      }

      // Encode deposit(bytes32 orderId)
      const orderIdHex = intent.order_id_hex;
      const data = depositData(orderIdHex);
      // amount_minor is on-chain wei

      setStatus("awaiting approval");
      const txHash = await blip.sendTransaction(
        { to: escrowAddress, value: BigInt(intent.amount_minor), data },
        provider
      );

      setStatus("confirming");
      const confirmRes = await fetch(
        `${apiBaseUrl}/payments/intent/${intent.id}/confirm`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ tx_hash: txHash }),
        }
      );
      if (!confirmRes.ok) {
        const e = await confirmRes.json().catch(() => ({}));
        throw new Error(e?.detail || e?.error?.message || "On-chain verification failed.");
      }
    } catch (err: any) {
      setError(err.message || "Checkout could not be completed.");
      setStatus("failed");
    } finally {
      setLoading(false);
    }
  };

  if (orderResult) {
    return (
      <PurchaseConfirmationModal
        isOpen={true}
        onClose={onClose}
        order={orderResult}
      />
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkout-modal-title"
    >
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Lock className="h-6 w-6" />
            </div>
            <div>
              <h3 id="checkout-modal-title" className="text-lg font-bold text-slate-900">
                Blip Pay & Quai Escrow Checkout
              </h3>
              <p className="text-xs text-slate-500">
                100% Scam-Free Campus Commerce — Funds locked until delivery is confirmed.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition-colors"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Item Summary Box */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <h4 className="font-bold text-slate-900 text-sm">{listing.title}</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Seller:{" "}
                <strong className="text-slate-700">
                  {listing.seller_name || "Verified Student"}
                </strong>{" "}
                (Trust Score: {listing.seller_trust_score ?? 60})
              </p>
            </div>
            <div className="text-right">
              <span className="text-lg font-extrabold text-slate-900">
                ₦{listing.price.toLocaleString("en-NG")}
              </span>
              <span className="text-[10px] block uppercase text-slate-400 font-semibold">
                NGN Fiat
              </span>
            </div>
          </div>

          {/* Escrow Guarantee Banner */}
          <div className="p-4 rounded-xl bg-primary-50 border border-primary-200 text-xs text-primary-900 space-y-2">
            <div className="flex items-center gap-1.5 font-bold">
              <ShieldCheck className="h-4 w-4 text-primary-600" />
              <span>How CampusOS Smart Escrow Works:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-primary-800">
              <li>
                Your payment is locked in the <strong>MarketplaceEscrow.sol</strong> Quai smart contract.
              </li>
              <li>The seller cannot withdraw until you inspect and confirm physical delivery.</li>
              <li>
                On release, you and the seller both earn <strong>+5 Trust Score</strong>!
              </li>
            </ul>
          </div>

          {status && !["idle","creating"].includes(status) && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
              Payment status: <strong>{status}</strong>
              {status === "pending" && " — awaiting provider confirmation. Do not close this window."}
            </div>
          )}
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2 text-xs text-red-800" role="alert">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCheckout}
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              <CreditCard className="h-4 w-4" />
              <span>{loading ? "Locking Escrow..." : "Pay with Blip Pay & Lock Escrow"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
