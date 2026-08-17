"use client";

import React, { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type Report = {
  id: string;
  reporter_id: string;
  reported_user_id: string;
  category: string;
  description: string;
  status: string;
  created_at: string;
  resolution_notes?: string | null;
};

export default function AdminFraudPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setReports(await adminFetch<Report[]>("/admin/fraud"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const resolve = async (id: string, confirmed: boolean) => {
    const notes = window.prompt(confirmed ? "Resolution notes (confirmed fraud):" : "Resolution notes (dismissed):");
    if (notes === null) return;
    await adminFetch(`/admin/fraud/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({
        status: confirmed ? "resolved_confirmed" : "resolved_dismissed",
        resolution_notes: notes || "Resolved by admin",
      }),
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
      {reports.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">No fraud reports.</p>
      ) : (
        reports.map((r) => (
          <div key={r.id} className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-bold text-slate-900">{r.category}</div>
                <p className="text-sm text-slate-600 mt-1 max-w-xl">{r.description}</p>
                <div className="mt-2 text-xs text-slate-400">
                  Reporter: <span className="font-mono">{r.reporter_id.slice(0, 8)}</span> · Reported:{" "}
                  <span className="font-mono">{r.reported_user_id.slice(0, 8)}</span>
                </div>
              </div>
              <div className="text-right">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold">{r.status}</span>
                {r.status === "pending" && (
                  <div className="mt-2 flex gap-2">
                    <button onClick={() => resolve(r.id, true)} className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-500">Confirm</button>
                    <button onClick={() => resolve(r.id, false)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-bold hover:bg-slate-50">Dismiss</button>
                  </div>
                )}
              </div>
            </div>
            {r.resolution_notes && <p className="mt-2 text-xs text-slate-500">{r.resolution_notes}</p>}
          </div>
        ))
      )}
    </div>
  );
}
