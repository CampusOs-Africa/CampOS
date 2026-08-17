"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Loader2, AlertCircle, CheckCircle, XCircle, RotateCcw, Ban } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type Verif = {
  id: string;
  user_id: string;
  university_email: string;
  status: string;
  student_id_url: string;
  admission_letter_url: string;
  created_at: string;
  rejection_reason?: string | null;
};

const filters = ["pending", "approved", "rejected", "resubmission_requested", "revoked"];

export default function AdminVerificationsPage() {
  const [items, setItems] = useState<Verif[]>([]);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminFetch<Verif[]>(
        `/admin/verifications${filter ? `?status=${filter}` : ""}`
      );
      setItems(data);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (id: string, action: "approve" | "reject" | "resubmit" | "revoke", reason?: string) => {
    if (action === "reject" || action === "resubmit" || action === "revoke") {
      const r = window.prompt(
        action === "revoke"
          ? "Reason for revocation?"
          : action === "reject"
          ? "Reason for rejection?"
          : "What should the student resubmit?"
      );
      if (r === null) return;
      reason = r;
    }
    if (!window.confirm(`Confirm '${action}' for this verification?`)) return;
    setBusy(id);
    try {
      if (action === "revoke") {
        await adminFetch(`/admin/verifications/revoke?user_id=${items.find((i) => i.id === id)?.user_id}`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        });
      } else {
        await adminFetch(`/admin/verifications/${id}/${action}`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        });
      }
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Action failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold ${
              filter === f ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex gap-2">
          <AlertCircle className="h-5 w-5" /> {error}
        </div>
      )}
      {loading ? (
        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">No verifications.</p>
      ) : (
        <div className="space-y-3">
          {items.map((v) => (
            <div key={v.id} className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-xs text-slate-400">{v.user_id}</div>
                  <div className="font-semibold text-slate-900">{v.university_email}</div>
                  <div className="mt-1 flex gap-3 text-xs text-slate-500">
                    <a href={v.student_id_url} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline">View student ID</a>
                    <a href={v.admission_letter_url} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline">View admission letter</a>
                  </div>
                  {v.rejection_reason && (
                    <p className="mt-2 text-xs text-red-600">Reason: {v.rejection_reason}</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button disabled={busy === v.id} onClick={() => act(v.id, "approve")} className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-500 disabled:opacity-50">
                    <CheckCircle className="h-4 w-4" /> Approve
                  </button>
                  <button disabled={busy === v.id} onClick={() => act(v.id, "reject")} className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-500 disabled:opacity-50">
                    <XCircle className="h-4 w-4" /> Reject
                  </button>
                  <button disabled={busy === v.id} onClick={() => act(v.id, "resubmit")} className="inline-flex items-center gap-1 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-400 disabled:opacity-50">
                    <RotateCcw className="h-4 w-4" /> Resubmit
                  </button>
                  {v.status === "approved" && (
                    <button disabled={busy === v.id} onClick={() => act(v.id, "revoke")} className="inline-flex items-center gap-1 rounded-lg border border-red-300 px-3 py-1.5 text-xs font-bold text-red-700 hover:bg-red-50 disabled:opacity-50">
                      <Ban className="h-4 w-4" /> Revoke
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
