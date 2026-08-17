"use client";

import React from "react";
import {
  ShieldCheck,
  Award,
  AlertTriangle,
  RefreshCcw,
  CheckCircle,
  FileText,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

export interface TrustHistoryItem {
  id: string;
  user_id: string;
  delta: number;
  old_score: number;
  new_score: number;
  event_type: string;
  reason: string;
  reference_id?: string | null;
  created_at: string;
}

interface TrustHistoryTimelineProps {
  history: TrustHistoryItem[];
}

export const TrustHistoryTimeline: React.FC<TrustHistoryTimelineProps> = React.memo(({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm text-slate-500 text-sm">
        No reputation audit events recorded yet.
      </div>
    );
  }

  const getEventBadge = (type: string, delta: number) => {
    if (delta > 0) {
      return {
        bg: "bg-emerald-50 text-emerald-800 border-emerald-200",
        icon: <TrendingUp className="h-4 w-4 text-emerald-600" />,
        label: `+${delta} pts`,
      };
    }
    return {
      bg: "bg-red-50 text-red-800 border-red-200",
      icon: <TrendingDown className="h-4 w-4 text-red-600" />,
      label: `${delta} pts`,
    };
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-100 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Immutable Reputation Audit Trail
        </h3>
        <span className="text-xs font-semibold text-slate-500">
          {history.length} Event(s) Recorded
        </span>
      </div>

      <div className="divide-y divide-slate-100">
        {history.map((item) => {
          const badge = getEventBadge(item.event_type, item.delta);
          const dateStr = new Date(item.created_at).toLocaleString("en-NG", {
            dateStyle: "medium",
            timeStyle: "short",
          });

          return (
            <div
              key={item.id}
              className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${badge.bg}`}
                  >
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>
                  <span className="text-xs font-bold text-slate-600 uppercase">
                    ● {item.event_type.replace("_", " ")}
                  </span>
                </div>
                <p className="text-sm font-semibold text-slate-900">{item.reason}</p>
                {item.reference_id && (
                  <p className="text-[11px] font-mono text-slate-400">
                    Ref ID: {item.reference_id}
                  </p>
                )}
              </div>

              <div className="text-right sm:shrink-0">
                <div className="text-sm font-extrabold text-slate-900">
                  {item.old_score} → <span className="text-primary-600">{item.new_score}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{dateStr}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

TrustHistoryTimeline.displayName = "TrustHistoryTimeline";
