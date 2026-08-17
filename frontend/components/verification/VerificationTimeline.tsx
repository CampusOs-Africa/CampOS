import React from "react";
import { CheckCircle2, Clock, AlertTriangle, FileText, UserCheck } from "lucide-react";

export interface VerificationHistoryItem {
  id: string;
  verification_id: string;
  user_id: string;
  old_status?: string;
  new_status: string;
  changed_by?: string;
  reason?: string;
  timestamp: string;
}

interface VerificationTimelineProps {
  history: VerificationHistoryItem[];
}

export const VerificationTimeline: React.FC<VerificationTimelineProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic py-4">
        No verification audit history recorded yet.
      </div>
    );
  }

  const getStepIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved":
      case "verified":
        return <CheckCircle2 className="h-5 w-5 text-emerald-600" />;
      case "rejected":
      case "revoked":
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case "resubmission_requested":
        return <FileText className="h-5 w-5 text-blue-500" />;
      default:
        return <Clock className="h-5 w-5 text-amber-500" />;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved":
      case "verified":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "rejected":
      case "revoked":
        return "bg-red-100 text-red-800 border-red-200";
      case "resubmission_requested":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-amber-100 text-amber-800 border-amber-200";
    }
  };

  return (
    <div className="flow-root">
      <ul role="list" className="-mb-8">
        {history.map((event, idx) => {
          const isLast = idx === history.length - 1;
          const formattedDate = new Date(event.timestamp).toLocaleString("en-NG", {
            dateStyle: "medium",
            timeStyle: "short",
          });

          return (
            <li key={event.id}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-slate-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex space-x-3">
                  <div>
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 ring-4 ring-white">
                      {getStepIcon(event.new_status)}
                    </span>
                  </div>
                  <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium border ${getStatusBadgeColor(
                            event.new_status
                          )}`}
                        >
                          {event.new_status.replace("_", " ").toUpperCase()}
                        </span>
                        {event.old_status && (
                          <span className="text-xs text-slate-400">
                            (from {event.old_status})
                          </span>
                        )}
                      </div>
                      {event.reason && (
                        <p className="mt-2 text-sm text-slate-700 bg-slate-50 p-3 rounded-md border border-slate-100">
                          {event.reason}
                        </p>
                      )}
                      {event.changed_by && (
                        <p className="mt-1 text-xs text-slate-400 flex items-center gap-1">
                          <UserCheck className="h-3 w-3" /> Actor ID: {event.changed_by}
                        </p>
                      )}
                    </div>
                    <div className="whitespace-nowrap text-right text-xs text-slate-400">
                      <time dateTime={event.timestamp}>{formattedDate}</time>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
