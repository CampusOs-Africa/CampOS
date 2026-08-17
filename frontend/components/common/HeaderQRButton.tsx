"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { QrCode } from "lucide-react";

const CampusIdentityScannerModal = dynamic(
  () =>
    import("../identity/CampusIdentityScannerModal").then(
      (mod) => mod.CampusIdentityScannerModal
    ),
  { ssr: false }
);

export const HeaderQRButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 transition-all shadow-sm"
        title="Scan Campus Identity QR Card (Merchants & Admins)"
      >
        <QrCode className="h-3.5 w-3.5 text-primary-600" />
        <span>Scan QR Card</span>
      </button>

      <CampusIdentityScannerModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        role="merchant"
      />
    </>
  );
};
