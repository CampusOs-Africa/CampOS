import React from "react";
import { ShieldCheck, Clock, AlertTriangle, ExternalLink, Key, Award, FileText } from "lucide-react";
import { VerificationBadge } from "./VerificationBadge";
import { VerificationTimeline, VerificationHistoryItem } from "./VerificationTimeline";
import { BlockchainStatusMonitor } from "./BlockchainStatusMonitor";
import { CampusIdentityQR } from "../identity/CampusIdentityQR";

interface StatusCardProps {
  userId: string;
  verificationStatus: string;
  trustScore: number;
  credentialHash?: string | null;
  approvedAt?: string | null;
  verificationRecord?: {
    id: string;
    student_id_url: string;
    admission_letter_url: string;
    university_email: string;
    rejection_reason?: string | null;
    tx_hash?: string | null;
  } | null;
  history?: VerificationHistoryItem[];
  onResubmitClick?: () => void;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  userId,
  verificationStatus,
  trustScore,
  credentialHash,
  approvedAt,
  verificationRecord,
  history = [],
  onResubmitClick,
}) => {
  const isVerified = verificationStatus === "verified" || verificationStatus === "approved";
  const isRejected = verificationStatus === "rejected";
  const isResubmission = verificationStatus === "resubmission_requested";

  return (
    <div className="space-y-6">
      {/* Overview Banner Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900">
                Student Verification Status
              </h2>
              <VerificationBadge status={verificationStatus} />
            </div>
            <p className="mt-1 text-sm text-slate-500">
              User ID: <span className="font-mono text-xs text-slate-700">{userId}</span>
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
            <Award className="h-5 w-5 text-amber-500" />
            <div>
              <p className="text-xs font-medium text-slate-500">Current Trust Score</p>
              <p className="text-lg font-bold text-slate-900">
                {trustScore} <span className="text-xs font-normal text-emerald-600">({isVerified ? "+10 Verified Bonus" : "Baseline"})</span>
              </p>
            </div>
          </div>
        </div>

        {/* Verification Description & Alert */}
        <div className="mt-6">
          {isVerified && (
            <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-4 flex items-start gap-3">
              <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-emerald-900">
                  Verified Student Identity Active
                </h4>
                <p className="mt-1 text-sm text-emerald-700">
                  Your credentials have been administratively approved and cryptographically registered on Quai Network. You now have full access to create marketplace listings and receive student discounts.
                </p>
              </div>
            </div>
          )}

          {(isRejected || isResubmission) && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-900">
                  {isResubmission ? "Resubmission Requested" : "Verification Rejected"}
                </h4>
                {verificationRecord?.rejection_reason && (
                  <p className="mt-1 text-sm text-red-800 font-medium">
                    Reason: {verificationRecord.rejection_reason}
                  </p>
                )}
                {onResubmitClick && (
                  <button
                    onClick={onResubmitClick}
                    className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-red-500"
                  >
                    Re-upload Verification Documents
                  </button>
                )}
              </div>
            </div>
          )}

          {verificationStatus === "pending" && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 flex items-start gap-3">
              <Clock className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-amber-900">
                  Documents Under Administrative Review
                </h4>
                <p className="mt-1 text-sm text-amber-800">
                  Your Student ID and admission letter are in the administrative queue. Review typically completes within 24 hours.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Permanent Signed Campus Identity QR Card (renders when verified/approved) */}
        {isVerified && (
          <div className="mt-6">
            <CampusIdentityQR
              userId={userId}
              status={verificationStatus}
              credentialId={credentialHash || verificationRecord?.tx_hash}
              timestamp={approvedAt}
            />
          </div>
        )}

        {/* Live Quai Blockchain Status Monitor (renders when verified/approved) */}
        {isVerified && (
          <BlockchainStatusMonitor
            userId={userId}
            initialTxHash={verificationRecord?.tx_hash}
            credentialHash={credentialHash}
          />
        )}

        {/* Cryptographic & On-Chain Details (when unverified/offline fallback) */}
        {!isVerified && credentialHash && (
          <div className="mt-6 p-4 rounded-lg bg-slate-900 text-slate-100 font-mono text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <Key className="h-4 w-4 text-primary-400" />
                SHA-256 Credential Hash (Stored on Quai Network StudentIdentity Contract):
              </span>
              <span className="text-emerald-400">● ON-CHAIN VERIFIED</span>
            </div>
            <div className="break-all bg-slate-800 p-2.5 rounded border border-slate-700 select-all">
              {credentialHash}
            </div>
            {approvedAt && (
              <div className="text-slate-400 text-right">
                Registered At: {new Date(approvedAt).toLocaleString("en-NG")}
              </div>
            )}
          </div>
        )}

        {/* Document URLs */}
        {verificationRecord && (
          <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <a
              href={verificationRecord.student_id_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-sm font-medium text-slate-700 transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" />
                Student ID Document
              </span>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </a>
            <a
              href={verificationRecord.admission_letter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-sm font-medium text-slate-700 transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" />
                Admission Letter
              </span>
              <ExternalLink className="h-4 w-4 text-slate-400" />
            </a>
          </div>
        )}
      </div>

      {/* Audit Timeline Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-6">
          Verification Audit Trail & History
        </h3>
        <VerificationTimeline history={history} />
      </div>
    </div>
  );
};
