"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect } from "react";
import {
  TrustScoreGauge,
  TrustHistoryTimeline,
  TrustLeaderboard,
  PeerReviewModal,
  FraudReportModal,
} from "../../components/trust";
import { Award, ShieldCheck, Trophy, Loader2, PlusCircle, AlertTriangle } from "lucide-react";

export default function TrustDashboardPage() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "leaderboard">("dashboard");
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [leaderboardData, setLeaderboardData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Default demo student user ID from verified seller identity
  const [userId] = useState("seller-verified-01");
  const [peerModalOpen, setPeerModalOpen] = useState(false);
  const [fraudModalOpen, setFraudModalOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [dashRes, boardRes] = await Promise.all([
          fetch(`${API_BASE_URL}/trust/dashboard/${userId}`),
          fetch(`${API_BASE_URL}/trust/leaderboard`),
        ]);
        if (!dashRes.ok || !boardRes.ok) {
          throw new Error("Failed to load Trust Score engine data from server.");
        }
        const [dashJson, boardJson] = await Promise.all([
          dashRes.json(),
          boardRes.json(),
        ]);
        setDashboardData(dashJson);
        setLeaderboardData(boardJson);
      } catch (err: any) {
        setError(err.message || "An error occurred fetching reputation data.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
        <p className="text-sm font-semibold">Loading Campus Trust Score Engine...</p>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <p className="text-base font-bold text-red-600">{error || "Reputation data unavailable."}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Award className="h-6 w-6 text-amber-500" />
            Campus Trust Score Engine (Milestone 6)
          </h1>
          <p className="text-sm text-slate-500">
            Verifiable reputation engine powered by Quai Network and Blip Pay. Every score change creates an immutable audit trail.
          </p>
        </div>

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

      {/* Navigation Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`px-5 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "dashboard"
              ? "bg-slate-900 text-white shadow-md"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          My Trust Score Gauge & Audit Trail
        </button>
        <button
          onClick={() => setActiveTab("leaderboard")}
          className={`inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "leaderboard"
              ? "bg-slate-900 text-white shadow-md"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Trophy className="h-3.5 w-3.5 text-amber-500" />
          <span>Campus Leaderboard</span>
        </button>
      </div>

      {/* Main Content Area */}
      {activeTab === "dashboard" ? (
        <div className="space-y-8">
          <TrustScoreGauge data={dashboardData} />
          <TrustHistoryTimeline history={dashboardData.history || []} />
        </div>
      ) : (
        <TrustLeaderboard entries={leaderboardData} />
      )}

      {/* Modals */}
      <PeerReviewModal
        isOpen={peerModalOpen}
        onClose={() => setPeerModalOpen(false)}
        revieweeId="student-peer-partner-02"
        revieweeName="Chidi Okafor"
        reviewerId={userId}
        onSuccess={() => window.location.reload()}
      />

      <FraudReportModal
        isOpen={fraudModalOpen}
        onClose={() => setFraudModalOpen(false)}
        reportedUserId="student-peer-partner-02"
        reportedUserName="Chidi Okafor"
        reporterId={userId}
        onSuccess={() => window.location.reload()}
      />
    </div>
  );
}
