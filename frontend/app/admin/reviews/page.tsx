"use client";

import React, { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type Review = {
  id: string;
  reviewer_id: string;
  reviewee_id: string;
  rating: number;
  comment?: string | null;
  status: string;
  created_at: string;
};

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setReviews(await adminFetch<Review[]>("/admin/reviews?status=flagged"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const moderate = async (id: string, status: string) => {
    const reason = window.prompt(`Reason for '${status}'?`) || "Moderated by admin";
    await adminFetch(`/admin/reviews/${id}/moderate`, {
      method: "POST",
      body: JSON.stringify({ status, reason }),
    });
    load();
  };

  if (loading) return <Loader2 className="h-5 w-5 animate-spin text-slate-400" />;
  if (error)
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex gap-2">
        <AlertCircle className="h-5 w-5" /> {error}
      </div>
    );

  return (
    <div className="space-y-3">
      {reviews.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">No flagged reviews.</p>
      ) : (
        reviews.map((r) => (
          <div key={r.id} className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm">
                  <span className="font-mono text-xs text-slate-400">{r.reviewer_id.slice(0, 8)}</span>
                  {" → "}
                  <span className="font-mono text-xs text-slate-400">{r.reviewee_id.slice(0, 8)}</span>
                </div>
                <div className="mt-1 text-amber-600">{"★".repeat(r.rating)}</div>
                <p className="mt-1 text-sm text-slate-700">{r.comment}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => moderate(r.id, "approved")} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-500">Approve</button>
                <button onClick={() => moderate(r.id, "removed")} className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-500">Remove</button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
