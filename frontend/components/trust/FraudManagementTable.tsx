"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { ShieldAlert, CheckCircle, XCircle, Loader2, ExternalLink } from "lucide-react";

export interface FraudReportItem {
  id: string;
  reporter_id: string;
  reported_user_id: string;
  category: string;
  description: string;
  evidence_url?: string | null;
  status: string;
  penalty_applied: number;
  created_at: string;
  reporter_name?: string | null;
  reported_user_name?: string | null;
}

interface FraudManagementTableProps {
  reports: FraudReportItem[];
  adminId: string;
  apiBaseUrl?: string;
  onResolveComplete?: () => void;
}

export const FraudManagementTable: React.FC<FraudManagementTableProps> = React.memo(
  ({
    reports,
    adminId,
    apiBaseUrl = API_BASE_URL,
    onResolveComplete,
  }) => {
    const [loadingId, setLoadingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleResolve = async (
      reportId: string,
      status: string,
      penaltyPoints: number
    ) => {
      setLoadingId(reportId);
      setError(null);
      try {
        const res = await fetch(
          `${apiBaseUrl}/fraud/reports/${reportId}/resolve?admin_id=${adminId}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              status,
              penalty_points: penaltyPoints,
              resolution_notes:
                status === "resolved_confirmed"
                  ? "Confirmed fraudulent behavior after investigation. Applied -20 Trust Score penalty."
                  : "Report dismissed after review. No penalty applied.",
            }),
          }
        );
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.error?.message || "Failed to resolve fraud report.");
        }
        if (onResolveComplete) onResolveComplete();
      } catch (err: any) {
        setError(err.message || "An error occurred resolving the report.");
      } finally {
        setLoadingId(null);
      }
    };

    const getStatusBadge = (status: string) => {
      switch (status.toLowerCase()) {
        case "resolved_confirmed":
          return "bg-red-100 text-red-800 border-red-300";
        case "resolved_dismissed":
          return "bg-slate-100 text-slate-700 border-slate-300";
        default:
          return "bg-amber-100 text-amber-800 border-amber-300";
      }
    };

    if (!reports || reports.length === 0) {
      return (
        <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm text-slate-500 text-sm font-semibold">
          No fraud reports pending review.
        </div>
      );
    }

    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-600" />
            <h3 className="text-base font-extrabold text-slate-900">
              Admin Fraud Governance & Dispute Resolution
            </h3>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {reports.length} Report(s) in Queue
          </span>
        </div>

        {error && (
          <div className="mx-5 p-3 rounded-xl bg-red-50 border border-red-200 text-xs font-semibold text-red-700">
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 text-xs uppercase tracking-wider bg-slate-50/70">
                <th className="py-3 px-5 font-bold">Reported User</th>
                <th className="py-3 px-5 font-bold">Category</th>
                <th className="py-3 px-5 font-bold">Description</th>
                <th className="py-3 px-5 font-bold">Status</th>
                <th className="py-3 px-5 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {reports.map((report) => {
                const isLoading = loadingId === report.id;
                const isResolved =
                  report.status === "resolved_confirmed" ||
                  report.status === "resolved_dismissed";

                return (
                  <tr key={report.id} className="hover:bg-slate-50/70">
                    <td className="py-4 px-5">
                      <div className="font-extrabold text-slate-900">
                        {report.reported_user_name || "Student Seller"}
                      </div>
                      <div className="text-xs text-slate-500">
                        Reporter: {report.reporter_name || "Buyer Student"}
                      </div>
                    </td>
                    <td className="py-4 px-5 font-semibold text-slate-700 uppercase text-xs">
                      {report.category.replace("_", " ")}
                    </td>
                    <td className="py-4 px-5 max-w-xs">
                      <p className="text-xs text-slate-700 line-clamp-2">
                        {report.description}
                      </p>
                      {report.evidence_url && (
                        <a
                          href={report.evidence_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-primary-600 font-bold hover:underline mt-1"
                        >
                          <span>View Evidence Proof</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </td>
                    <td className="py-4 px-5">
                      <span
                        className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold border ${getStatusBadge(
                          report.status
                        )}`}
                      >
                        ● {report.status.replace("_", " ").toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-right space-x-2">
                      {!isResolved ? (
                        <>
                          <button
                            onClick={() =>
                              handleResolve(report.id, "resolved_confirmed", 20)
                            }
                            disabled={isLoading}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-sm disabled:opacity-50"
                          >
                            {isLoading && (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            )}
                            <span>Confirm Fraud (-20 pts)</span>
                          </button>
                          <button
                            onClick={() =>
                              handleResolve(report.id, "resolved_dismissed", 0)
                            }
                            disabled={isLoading}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs disabled:opacity-50"
                          >
                            <span>Dismiss</span>
                          </button>
                        </>
                      ) : (
                        <span className="text-xs font-semibold text-slate-400">
                          Resolved
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
);

FraudManagementTable.displayName = "FraudManagementTable";
