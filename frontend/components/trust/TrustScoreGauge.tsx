"use client";

import React from "react";
import { Award, TrendingUp, TrendingDown, CheckCircle2, Star } from "lucide-react";

interface TrustDashboardData {
  user_id: string;
  name: string;
  email: string;
  verification_status: string;
  trust_score: number;
  trust_badge: string;
  total_positive_earned: number;
  total_penalties_deducted: number;
  completed_sales: number;
  peer_reviews_count: number;
  average_rating: number;
}

interface TrustScoreGaugeProps {
  data: TrustDashboardData;
}

export const TrustScoreGauge: React.FC<TrustScoreGaugeProps> = React.memo(({ data }) => {
  const getBadgeColor = (badge: string) => {
    switch (badge.toLowerCase()) {
      case "platinum":
        return "bg-gradient-to-r from-slate-200 to-slate-400 text-slate-900 border-slate-300";
      case "gold":
        return "bg-gradient-to-r from-amber-300 to-amber-500 text-slate-950 border-amber-400";
      case "silver":
        return "bg-gradient-to-r from-slate-300 to-slate-500 text-white border-slate-400";
      case "bronze":
        return "bg-gradient-to-r from-amber-700 to-amber-900 text-amber-100 border-amber-800";
      default:
        return "bg-gradient-to-r from-red-600 to-red-800 text-white border-red-700";
    }
  };

  const getScoreTextColor = (score: number) => {
    if (score >= 85) return "text-purple-400";
    if (score >= 70) return "text-amber-400";
    if (score >= 55) return "text-blue-400";
    if (score >= 40) return "text-emerald-400";
    return "text-red-400";
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl border border-slate-700 p-6 sm:p-8 text-white shadow-xl space-y-6">
      {/* Top bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-700/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Award className="h-6 w-6 text-amber-400" />
            <h2 className="text-xl font-extrabold tracking-tight">Campus Trust Score Gauge</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Verifiable reputation engine (0–100 bounded scale). Baseline starting score is 50.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`px-4 py-1.5 rounded-full text-xs font-extrabold uppercase tracking-wider border shadow-sm ${getBadgeColor(
              data.trust_badge
            )}`}
          >
            ● {data.trust_badge} Tier
          </span>
        </div>
      </div>

      {/* Main radial score and stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
        {/* Score display */}
        <div className="md:col-span-1 flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-800/80 border border-slate-700 text-center">
          <span className={`text-5xl font-black ${getScoreTextColor(data.trust_score)}`}>
            {data.trust_score}
          </span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">
            Out of 100
          </span>
        </div>

        {/* Breakdown counters */}
        <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
              <TrendingUp className="h-3.5 w-3.5" />
              <span>Positive Earned</span>
            </div>
            <div className="text-xl font-extrabold text-white">
              +{data.total_positive_earned}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-red-400">
              <TrendingDown className="h-3.5 w-3.5" />
              <span>Penalties Deducted</span>
            </div>
            <div className="text-xl font-extrabold text-white">
              -{data.total_penalties_deducted}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Escrow Sales</span>
            </div>
            <div className="text-xl font-extrabold text-white">
              {data.completed_sales}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400">
              <Star className="h-3.5 w-3.5" />
              <span>Peer Reviews</span>
            </div>
            <div className="text-xl font-extrabold text-white">
              {data.peer_reviews_count} <span className="text-xs text-slate-400">({data.average_rating}★)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

TrustScoreGauge.displayName = "TrustScoreGauge";
