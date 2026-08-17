"use client";
import { API_BASE_URL } from "../../../lib/api";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

const CheckoutModal = dynamic(
  () =>
    import("../../../components/marketplace/CheckoutModal").then(
      (mod) => mod.CheckoutModal
    ),
  { ssr: false }
);

export default function CheckoutPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [buyerId, setBuyerId] = useState("buyer-demo-001");

  useEffect(() => {
    if (!id) return;
    const fetchListing = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `${API_BASE_URL}/marketplace/listings/${id}`
        );
        if (!res.ok) {
          throw new Error("Failed to load listing details. It may not exist or is unavailable.");
        }
        const data = await res.json();
        setListing(data);
      } catch (err: any) {
        setError(err.message || "Could not prepare Blip Pay checkout intent.");
      } finally {
        setLoading(false);
      }
    };
    fetchListing();
  }, [id]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
        <p className="text-sm font-semibold">Preparing Blip Pay checkout intent...</p>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <p className="text-base font-bold text-red-600">{error || "Listing unavailable."}</p>
        <Link
          href="/marketplace"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Marketplace</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <Link
        href={`/marketplace/${id}`}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Item Details</span>
      </Link>

      <CheckoutModal
        isOpen={true}
        onClose={() => router.push(`/marketplace/${id}`)}
        listing={listing}
        buyerId={buyerId}
        onSuccess={() => router.push("/orders")}
      />
    </div>
  );
}
