"use client";
import { API_BASE_URL } from "../../../lib/api";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  TrustScoreGauge,
  TrustHistoryTimeline,
  PeerReviewModal,
  FraudReportModal,
} from "../../../components/trust";
import {
  Award,
  ShieldCheck,
  ArrowLeft,
  Loader2,
  PlusCircle,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";

export default function PublicTrustProfilePage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Demo logged-in student UUID viewing another student profile
  const [viewerId] = useState("buyer-demo-001");
  const [peerModalOpen, setPeerModalOpen] = useState(false);
  const [fraudModalOpen, setFraudModalOpen] = useState(false);

  useEffect(() => {
    if (!id) return;
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/trust/dashboard/${id}`);
        if (!res.ok) {
          throw new Error("Failed to load student trust profile.");
        }
        const json = await res.json();
        setDashboardData(json);
      } catch (err: any) {
        setError(err.message || "Could not fetch reputation profile.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [id]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
        <p className="text-sm font-semibold">Loading Student Trust Profile...</p>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <p className="text-base font-bold text-red-600">{error || "Trust profile not found."}</p>
        <Link
          href="/trust"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Trust Engine</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/trust"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Campus Trust Dashboard</span>
        </Link>

        {/* Peer review and Fraud report actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPeerModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-bold text-white shadow-sm transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Submit Peer Review</span>
          </button>
          <button
            onClick={() => setFraudModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-xs font-bold text-red-700 border border-red-200 transition-all shadow-sm"
          >
            <AlertTriangle className="h-4 w-4" />
            <span>Report Fraud</span>
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900">{dashboardData.name}</h1>
            {dashboardData.verification_status === "verified" && (
              <span title="Verified Student Identity">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{dashboardData.email}</p>
        </div>

        <div className="text-right">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
            Reputation Tier
          </span>
          <span className="text-lg font-black text-slate-900">
            ● {dashboardData.trust_badge}
          </span>
        </div>
      </div>

      <TrustScoreGauge data={dashboardData} />
      <TrustHistoryTimeline history={dashboardData.history || []} />

      <PeerReviewModal
        isOpen={peerModalOpen}
        onClose={() => setPeerModalOpen(false)}
        revieweeId={dashboardData.user_id}
        revieweeName={dashboardData.name}
        reviewerId={viewerId}
        onSuccess={() => window.location.reload()}
      />

      <FraudReportModal
        isOpen={fraudModalOpen}
        onClose={() => setFraudModalOpen(false)}
        reportedUserId={dashboardData.user_id}
        reportedUserName={dashboardData.name}
        reporterId={viewerId}
        onSuccess={() => window.location.reload()}
      />
    </div>
  );
}
