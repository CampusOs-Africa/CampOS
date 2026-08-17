"use client";

import React, { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type Order = {
  id: string;
  buyer_id: string;
  seller_id: string;
  amount: number;
  status: string;
  created_at: string;
  escrow?: { state: string } | null;
};

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    adminFetch<Order[]>(`/admin/orders${status ? `?status=${status}` : ""}`)
      .then(setOrders)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed"))
      .finally(() => setLoading(false));
  }, [status]);

  if (loading) return <Loader2 className="h-5 w-5 animate-spin text-slate-400" />;
  if (error)
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex gap-2">
        <AlertCircle className="h-5 w-5" /> {error}
      </div>
    );

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {["", "initiated", "escrow_locked", "completed", "disputed", "cancelled"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatus(s)}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold ${
              status === s ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {s || "all"}
          </button>
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="p-3">Order</th>
              <th className="p-3">Buyer</th>
              <th className="p-3">Seller</th>
              <th className="p-3">Amount</th>
              <th className="p-3">Status</th>
              <th className="p-3">Escrow</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((o) => (
              <tr key={o.id}>
                <td className="p-3 font-mono text-xs">{o.id.slice(0, 8)}</td>
                <td className="p-3 font-mono text-xs text-slate-500">{o.buyer_id.slice(0, 8)}</td>
                <td className="p-3 font-mono text-xs text-slate-500">{o.seller_id.slice(0, 8)}</td>
                <td className="p-3">{o.amount}</td>
                <td className="p-3">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold">{o.status}</span>
                </td>
                <td className="p-3 text-xs text-slate-500">{o.escrow?.state ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
