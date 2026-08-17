"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ListingGrid } from "../../components/marketplace/ListingGrid";
import { ShoppingBag, ShieldCheck, PlusCircle, AlertCircle } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const ListingFormModal = dynamic(
  () =>
    import("../../components/marketplace/ListingFormModal").then(
      (mod) => mod.ListingFormModal
    ),
  { ssr: false }
);

export default function MarketplacePage() {
  const { user } = useAuth();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [showGate, setShowGate] = useState(false);

  const isVerified =
    user &&
    ["verified", "approved"].includes(user.verification_status || "");

  const handleSellClick = () => {
    if (!user) {
      setShowGate(true);
      return;
    }
    if (!isVerified) {
      setShowGate(true);
      return;
    }
    setCreateModalOpen(true);
  };

  return (
    <div className="space-y-8">
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <ShoppingBag className="h-6 w-6 text-primary-600" />
            Campus Marketplace
          </h1>
          <p className="text-sm text-slate-500">
            Anyone can browse and buy. Only verified students can sell.
          </p>
        </div>

        <button
          onClick={handleSellClick}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-bold text-white shadow-sm transition-all"
        >
          <PlusCircle className="h-4 w-4" />
          <span>+ List Item for Sale</span>
        </button>
      </div>

      {showGate && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-900">
            <p className="font-bold">
              Only verified students can sell on CampusOS.
            </p>
            <p className="mt-1">
              {!user
                ? "Please log in or create an account, then complete your student verification."
                : "Complete your student profile and submit verification for admin approval."}
            </p>
            <div className="mt-3 flex gap-2">
              {!user ? (
                <Link
                  href="/login"
                  className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold"
                >
                  Log in
                </Link>
              ) : (
                <Link
                  href="/create-profile"
                  className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold"
                >
                  Complete Student Verification
                </Link>
              )}
              <button
                onClick={() => setShowGate(false)}
                className="px-3 py-1.5 rounded-lg border border-amber-300 text-amber-900 text-xs font-bold hover:bg-amber-100"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      <ListingGrid onCreateClick={handleSellClick} />

      {user && isVerified && (
        <ListingFormModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          sellerId={user.id}
          onSuccess={() => {
            setCreateModalOpen(false);
            window.location.reload();
          }}
        />
      )}
    </div>
  );
}
