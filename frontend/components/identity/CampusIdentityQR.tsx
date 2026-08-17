"use client";

import React, { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  ShieldCheck,
  QrCode,
  Key,
  Calendar,
  Copy,
  Check,
  Award,
  ExternalLink,
} from "lucide-react";
import { VerificationBadge } from "../verification/VerificationBadge";

export interface CampusIdentityQRProps {
  userId: string;
  status?: string;
  credentialId?: string | null;
  timestamp?: string | null;
  signature?: string | null;
  payloadString?: string | null;
  size?: number;
  className?: string;
  showDetails?: boolean;
}

export const CampusIdentityQR: React.FC<CampusIdentityQRProps> = ({
  userId,
  status = "verified",
  credentialId = "0xquai_on_chain_credential",
  timestamp = new Date().toISOString(),
  signature = "a3f5b7c9d1e2...hmac-sha256-signature",
  payloadString,
  size = 150,
  className = "",
  showDetails = true,
}) => {
  const [copied, setCopied] = useState(false);

  // Construct QR payload JSON string for scanner verification
  const qrValue =
    payloadString ||
    JSON.stringify({
      user_id: userId,
      status: status,
      credential_id: credentialId,
      timestamp: timestamp,
      signature: signature,
    });

  const handleCopyId = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedDate = timestamp
    ? new Date(timestamp).toLocaleDateString("en-NG", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "N/A";

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden ${className}`}
    >
      <div className="flex flex-col sm:flex-row items-center sm:items-start justify-between gap-6">
        {/* Left Col: Scannable QR SVG */}
        <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-xl border border-slate-200 shadow-inner shrink-0">
          <div className="p-3 bg-white rounded-lg border border-slate-100 shadow-sm">
            <QRCodeSVG
              value={qrValue}
              size={size}
              level="H"
              includeMargin={false}
            />
          </div>
          <div className="mt-3 text-center">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-primary-50 text-primary-700 text-[11px] font-bold uppercase tracking-wider border border-primary-100">
              <QrCode className="h-3 w-3" /> Permanent QR ID
            </span>
          </div>
        </div>

        {/* Right Col: Encoded Credentials & Digital Signature Proof */}
        {showDetails && (
          <div className="flex-1 space-y-3.5 w-full">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  Campus Identity QR Credential
                </h4>
                <p className="text-xs text-slate-500">
                  Cryptographically signed permanent campus credential.
                </p>
              </div>
              <VerificationBadge status={status} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 font-medium block">Student UUID</span>
                <div className="font-mono font-semibold text-slate-800 flex items-center justify-between mt-0.5">
                  <span className="truncate">{userId}</span>
                  <button
                    onClick={() => handleCopyId(userId)}
                    className="text-primary-600 hover:text-primary-500 shrink-0 ml-2"
                  >
                    {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                  </button>
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 font-medium block">Verified At</span>
                <div className="font-semibold text-slate-800 flex items-center gap-1 mt-0.5">
                  <Calendar className="h-3 w-3 text-slate-400" />
                  {formattedDate}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs">
              <span className="text-slate-400 font-medium block">
                Blockchain Credential ID (Quai Network)
              </span>
              <div className="font-mono text-[11px] text-slate-700 break-all mt-0.5 select-all">
                {credentialId}
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900 text-slate-100 text-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="flex items-center gap-1 text-[11px]">
                  <Key className="h-3 w-3 text-primary-400" /> HMAC-SHA256 Digital Signature
                </span>
                <span className="text-[10px] text-emerald-400 font-semibold">
                  ● SIGNED PROOF
                </span>
              </div>
              <div className="font-mono text-[10px] text-emerald-300 break-all select-all">
                {signature}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
