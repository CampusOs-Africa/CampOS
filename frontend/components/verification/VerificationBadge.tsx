import React from "react";
import { ShieldCheck, Clock, AlertCircle, RefreshCw } from "lucide-react";

interface VerificationBadgeProps {
  status?: string;
  showLabel?: boolean;
  className?: string;
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({
  status = "pending",
  showLabel = true,
  className = "",
}) => {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "verified" || normalizedStatus === "approved") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-semibold text-primary-700 border border-primary-100 ${className}`}
        title="Verified Student Identity on Quai Network"
      >
        <ShieldCheck className="h-3.5 w-3.5 text-primary-600" />
        {showLabel && <span>Verified Student</span>}
      </span>
    );
  }

  if (normalizedStatus === "pending") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 border border-amber-200 ${className}`}
        title="Verification Under Administrative Review"
      >
        <Clock className="h-3.5 w-3.5 text-amber-500" />
        {showLabel && <span>Pending Verification</span>}
      </span>
    );
  }

  if (normalizedStatus === "resubmission_requested") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 border border-blue-200 ${className}`}
        title="Please review uploader instructions and re-submit"
      >
        <RefreshCw className="h-3.5 w-3.5 text-blue-500" />
        {showLabel && <span>Resubmission Needed</span>}
      </span>
    );
  }

  if (normalizedStatus === "rejected" || normalizedStatus === "revoked") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 border border-red-200 ${className}`}
        title="Verification was rejected or revoked"
      >
        <AlertCircle className="h-3.5 w-3.5 text-red-500" />
        {showLabel && <span>{normalizedStatus === "revoked" ? "Revoked" : "Rejected"}</span>}
      </span>
    );
  }

  return null;
};
