"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect, useCallback } from "react";
import { EscrowActions } from "../../components/marketplace/EscrowActions";
import {
  ShoppingBag,
  User,
  ShieldCheck,
  ExternalLink,
  Loader2,
  RefreshCw,
  Award,
  CheckCircle2,
  Star,
} from "lucide-react";

export default function MyOrdersPage() {
  const [activeTab, setActiveTab] = useState<"buyer" | "seller">("buyer");
  const [userId, setUserId] = useState("buyer-demo-001");
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review modal state
  const [reviewOrder, setReviewOrder] = useState<any | null>(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/orders/${activeTab}/${userId}`
      );
      if (!res.ok) {
        throw new Error(`Failed to load ${activeTab} orders.`);
      }
      const data = await res.json();
      setOrders(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || "Error loading orders.");
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }, [activeTab, userId]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewOrder) return;
    setReviewLoading(true);
    setReviewSuccess(null);
    try {
      const res = await fetch(`${API_BASE_URL}/reviews/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: reviewOrder.id,
          reviewer_id: userId,
          reviewee_id:
            activeTab === "buyer" ? reviewOrder.seller_id : reviewOrder.buyer_id,
          rating: rating,
          comment: comment.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(
          data?.error?.message || "Failed to submit reputation review."
        );
      }

      setReviewSuccess(
        `Review submitted! +2 Trust Score awarded to ${
          activeTab === "buyer" ? reviewOrder.seller_name : reviewOrder.buyer_name
        }.`
      );
      setTimeout(() => {
        setReviewOrder(null);
        setComment("");
        setReviewSuccess(null);
        fetchOrders();
      }, 1500);
    } catch (err: any) {
      alert(err.message || "Could not submit review.");
    } finally {
      setReviewLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header & User Picker */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ShoppingBag className="h-6 w-6 text-primary-600" />
            My Orders & Quai Escrow
          </h1>
          <p className="text-sm text-slate-500">
            Confirm item delivery to release escrow funds on Quai Network and earn +5 Trust Score.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
          <User className="h-4 w-4 text-slate-500" />
          <span className="text-xs text-slate-500">Demo User ID:</span>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="bg-white border border-slate-300 rounded px-2 py-0.5 text-xs font-mono text-slate-800 w-36 focus:outline-none focus:border-primary-500"
          />
          <button
            onClick={fetchOrders}
            className="p-1 rounded bg-white border border-slate-300 hover:bg-slate-50 text-slate-600"
            title="Refresh Orders"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("buyer")}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === "buyer"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          My Purchases (Buyer)
        </button>
        <button
          onClick={() => setActiveTab("seller")}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === "seller"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          My Sales (Seller)
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs font-semibold text-red-800">
          {error}
        </div>
      )}

      {/* Order Cards */}
      {loading ? (
        <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
          <p className="text-sm font-semibold">Loading orders and escrow state...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="p-16 text-center text-sm text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm italic">
          No orders found for this user in the '{activeTab}' role.
        </div>
      ) : (
        <div className="space-y-6">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8 space-y-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-primary-600">
                    Order #{order.id.slice(0, 8)}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 mt-0.5">
                    {order.listing_title || "Marketplace Item"}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {activeTab === "buyer"
                      ? `Seller: ${order.seller_name || order.seller_id}`
                      : `Buyer: ${order.buyer_name || order.buyer_id}`}
                    {" ● "}
                    Ref: <span className="font-mono">{order.payment_reference}</span>
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xl font-extrabold text-slate-900 block">
                    ₦{order.amount.toLocaleString("en-NG")}
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 uppercase mt-0.5">
                    <ShieldCheck className="h-3.5 w-3.5" /> Quai Escrow Protected
                  </span>
                </div>
              </div>

              {/* Escrow Hash */}
              {order.escrow_tx_hash && (
                <div className="p-3.5 rounded-xl bg-slate-900 text-slate-200 text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <span className="text-slate-400 block text-[11px]">
                      Quai Network Escrow Contract Transaction Receipt:
                    </span>
                    <span className="text-emerald-300 break-all">
                      {order.escrow_tx_hash}
                    </span>
                  </div>
                  <a
                    href={`https://testnet.quaiscan.io/tx/${order.escrow_tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-semibold text-[11px] shrink-0"
                  >
                    <span>Quai Receipt</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}

              {/* Escrow Action Bar */}
              <EscrowActions
                orderId={order.id}
                orderStatus={order.status}
                actorId={userId}
                onActionComplete={fetchOrders}
              />

              {/* Review button if completed */}
              {order.status === "completed" && (
                <div className="pt-2 border-t border-slate-100 flex justify-end">
                  <button
                    onClick={() => setReviewOrder(order)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-white font-bold text-xs shadow-sm transition-all"
                  >
                    <Star className="h-4 w-4 fill-white" />
                    <span>
                      Leave Review for{" "}
                      {activeTab === "buyer" ? order.seller_name : order.buyer_name}{" "}
                      (+2 Trust Score)
                    </span>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Review Dialog Modal */}
      {reviewOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
            <h3 className="text-lg font-bold text-slate-900">
              Submit Reputation Review
            </h3>
            <p className="text-xs text-slate-500">
              Rate your transaction with{" "}
              <strong>
                {activeTab === "buyer"
                  ? reviewOrder.seller_name
                  : reviewOrder.buyer_name}
              </strong>
              . Ratings of 4 or 5 stars award an automatic <strong>+2 Trust Score</strong>!
            </p>

            {reviewSuccess && (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
                {reviewSuccess}
              </div>
            )}

            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-2">
                  Star Rating (1 to 5)
                </label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      type="button"
                      key={s}
                      onClick={() => setRating(s)}
                      className={`h-10 w-10 rounded-xl font-bold flex items-center justify-center transition-all ${
                        s <= rating
                          ? "bg-amber-500 text-white shadow-md"
                          : "bg-slate-100 text-slate-400 hover:bg-slate-200"
                      }`}
                    >
                      {s} ★
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Comment (Optional)
                </label>
                <textarea
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="How was the item quality, communication, and pickup?"
                  className="w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => {
                    setReviewOrder(null);
                    setComment("");
                    setReviewSuccess(null);
                  }}
                  disabled={reviewLoading}
                  className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewLoading}
                  className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
                >
                  {reviewLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  <span>Submit Review</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
