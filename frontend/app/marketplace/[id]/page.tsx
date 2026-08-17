"use client";
import { API_BASE_URL } from "../../../lib/api";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ImageGallery } from "../../../components/marketplace/ImageGallery";
import { SellerProfileCard } from "../../../components/marketplace/SellerProfileCard";
import dynamic from "next/dynamic";
import { VerificationBadge } from "../../../components/verification/VerificationBadge";
import {
  ShieldCheck,
  CreditCard,
  ArrowLeft,
  Loader2,
  Lock,
  Edit3,
  Trash2,
  Package,
} from "lucide-react";
import Link from "next/link";

const ListingEditModal = dynamic(
  () =>
    import("../../../components/marketplace/ListingEditModal").then(
      (mod) => mod.ListingEditModal
    ),
  { ssr: false }
);

const DeleteConfirmModal = dynamic(
  () =>
    import("../../../components/marketplace/DeleteConfirmModal").then(
      (mod) => mod.DeleteConfirmModal
    ),
  { ssr: false }
);

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit and Delete modals state
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  // Current demo user ID (seller-verified-01 is owner of demo listings)
  const [actorId, setActorId] = useState("seller-verified-01");

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
          throw new Error("Failed to load listing details. Item may not exist.");
        }
        const data = await res.json();
        setListing(data);
      } catch (err: any) {
        setError(err.message || "Could not fetch marketplace item.");
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
        <p className="text-sm font-semibold">Loading marketplace item...</p>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <p className="text-base font-bold text-red-600">{error || "Listing not found."}</p>
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
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          href="/marketplace"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Marketplace Catalog</span>
        </Link>

        {/* Owner / Admin Management Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-all shadow-sm"
          >
            <Edit3 className="h-3.5 w-3.5 text-blue-600" />
            <span>Edit Listing</span>
          </button>
          <button
            onClick={() => setDeleteOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-xs font-semibold text-red-700 transition-all shadow-sm"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 cols: Image Gallery & Details */}
        <div className="lg:col-span-2 space-y-6">
          <ImageGallery images={listing.images} title={listing.title} />

          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-slate-900 text-white text-xs font-bold uppercase tracking-wider">
                  {listing.category}
                </span>
                <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold uppercase">
                  {listing.condition.replace("_", " ")}
                </span>
                <VerificationBadge status={listing.status} />
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                <Package className="h-3.5 w-3.5" />
                <span>In Stock: {listing.inventory_count || 1}</span>
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              {listing.title}
            </h1>

            <div className="text-2xl sm:text-3xl font-extrabold text-primary-600">
              ₦{listing.price.toLocaleString("en-NG")}
            </div>

            <div className="pt-4 border-t border-slate-100 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Item Description & Pickup Details
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                {listing.description}
              </p>
            </div>
          </div>
        </div>

        {/* Right col: Seller Profile & Buy Action Box */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider">
              <Lock className="h-4 w-4 text-emerald-600" />
              <span>Quai Escrow Guarantee</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Your payment is processed securely by <strong>Blip Pay</strong> and locked in the <strong>MarketplaceEscrow.sol</strong> smart contract on Quai Network until you inspect and confirm delivery.
            </p>

            {listing.status === "active" && (listing.inventory_count || 1) > 0 ? (
              <Link
                href={`/checkout/${listing.id}`}
                className="w-full py-3.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-sm shadow-lg flex items-center justify-center gap-2 transition-all"
              >
                <CreditCard className="h-4 w-4" />
                <span>Buy with Blip Pay & Lock Escrow</span>
              </Link>
            ) : (
              <button
                disabled
                className="w-full py-3.5 rounded-xl bg-slate-200 text-slate-500 font-bold text-sm cursor-not-allowed uppercase"
              >
                Item {listing.status === "sold" ? "Sold Out" : "Unavailable"}
              </button>
            )}
          </div>

          <SellerProfileCard sellerId={listing.seller_id} />
        </div>
      </div>

      {/* Edit Listing Modal */}
      <ListingEditModal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        listing={listing}
        actorId={actorId}
        onSuccess={() => {
          setEditOpen(false);
          window.location.reload();
        }}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        listingId={listing.id}
        listingTitle={listing.title}
        actorId={actorId}
        onSuccess={() => {
          setDeleteOpen(false);
          router.push("/marketplace");
        }}
      />
    </div>
  );
}
