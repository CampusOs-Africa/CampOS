"use client";

import React, { useEffect, useState } from "react";
import { Loader2, AlertCircle, Ban, RotateCcw } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type Listing = {
  id: string;
  seller_id: string;
  title: string;
  category: string;
  price: number;
  status: string;
  created_at: string;
};

export default function AdminListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const qs = status ? `?status=${status}` : "";
      setListings(await adminFetch<Listing[]>(`/admin/listings${qs}`));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, [status]);

  const moderate = async (id: string, suspend: boolean) => {
    if (!window.confirm(suspend ? "Suspend this listing?" : "Restore this listing?")) return;
    await adminFetch(`/admin/listings/${id}/${suspend ? "suspend" : "restore"}`, {
      method: "POST",
      body: JSON.stringify({ reason: suspend ? "Admin moderation" : "Restored by admin" }),
    });
    load();
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["", "active", "suspended", "sold"].map((s) => (
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
      {loading ? (
        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex gap-2">
          <AlertCircle className="h-5 w-5" /> {error}
        </div>
      ) : listings.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">No listings.</p>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="p-3">Title</th>
                <th className="p-3">Seller</th>
                <th className="p-3">Price</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {listings.map((l) => (
                <tr key={l.id}>
                  <td className="p-3 font-medium text-slate-800">{l.title}</td>
                  <td className="p-3 font-mono text-xs text-slate-500">{l.seller_id.slice(0, 8)}</td>
                  <td className="p-3">{l.price}</td>
                  <td className="p-3">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold">{l.status}</span>
                  </td>
                  <td className="p-3 text-right">
                    {l.status === "suspended" ? (
                      <button onClick={() => moderate(l.id, false)} className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-2 py-1 text-xs font-bold hover:bg-slate-50">
                        <RotateCcw className="h-3.5 w-3.5" /> Restore
                      </button>
                    ) : (
                      <button onClick={() => moderate(l.id, true)} className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-2 py-1 text-xs font-bold text-white hover:bg-red-500">
                        <Ban className="h-3.5 w-3.5" /> Suspend
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
