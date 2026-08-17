"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { AlertTriangle, Loader2, X, ShieldAlert } from "lucide-react";

interface FraudReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportedUserId: string;
  reportedUserName: string;
  reporterId: string;
  orderId?: string | null;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const FraudReportModal: React.FC<FraudReportModalProps> = ({
  isOpen,
  onClose,
  reportedUserId,
  reportedUserName,
  reporterId,
  orderId,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [category, setCategory] = useState("scam_listing");
  const [description, setDescription] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("https://res.cloudinary.com/demo/image/upload/sample.jpg");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/fraud/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reporter_id: reporterId,
          reported_user_id: reportedUserId,
          category,
          description,
          evidence_url: evidenceUrl,
          order_id: orderId || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || "Failed to submit fraud report.");
      }
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "An error occurred submitting the fraud report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-600" />
            <h3 className="text-lg font-bold text-slate-900">
              Submit Formal Fraud / Scam Report
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          Reporting <strong>{reportedUserName}</strong> for scam or fraudulent activity. Confirmed reports result in an automatic <strong>-20 Trust Score</strong> deduction and account restriction.
        </p>

        {error && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs font-semibold text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Fraud Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-900 bg-white focus:border-red-500 focus:outline-none font-semibold"
            >
              <option value="scam_listing">Scam Listing / Non-Existent Housing</option>
              <option value="fake_item">Counterfeit / Defective Item</option>
              <option value="non_delivery">Non-Delivery After Payment</option>
              <option value="identity_fraud">Identity / Credential Impersonation</option>
              <option value="other">Other Campus Policy Violation</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Detailed Explanation & Proof
            </label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide specific meetup details, messages, or discrepancy information..."
              className="w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-900 focus:border-red-500 focus:outline-none"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              <span>Submit Fraud Report</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
