"use client";
import { API_BASE_URL } from "../../../lib/api";

import React, { useState, useEffect, useCallback } from "react";
import { ListingCard, MarketplaceListingItem } from "../../../components/marketplace/ListingCard";
import { ListingFormModal } from "../../../components/marketplace/ListingFormModal";
import { ListingEditModal } from "../../../components/marketplace/ListingEditModal";
import { DeleteConfirmModal } from "../../../components/marketplace/DeleteConfirmModal";
import {
  ShoppingBag,
  PlusCircle,
  Edit3,
  Trash2,
  Loader2,
  RefreshCw,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";

export default function MyListingsPage() {
  const [sellerId, setSellerId] = useState("seller-verified-01");
  const [listings, setListings] = useState<MarketplaceListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [createOpen, setCreateOpen] = useState(false);
  const [editListing, setEditListing] = useState<MarketplaceListingItem | null>(null);
  const [deleteListing, setDeleteListing] = useState<MarketplaceListingItem | null>(null);

  const fetchMyListings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/marketplace/listings?seller_id=${sellerId}&status=`
      );
      if (!res.ok) {
        throw new Error("Failed to load seller listings.");
      }
      const data = await res.json();
      setListings(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || "Error fetching seller items.");
    } finally {
      setLoading(false);
    }
  }, [sellerId]);

  useEffect(() => {
    fetchMyListings();
  }, [fetchMyListings]);

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ShoppingBag className="h-6 w-6 text-primary-600" />
            My Marketplace Listings
          </h1>
          <p className="text-sm text-slate-500">
            Manage your active, pending, and sold items. Protected by Quai Escrow.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/marketplace"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Catalog</span>
          </Link>

          <button
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-bold text-white shadow-sm transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>+ List New Item</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs font-semibold text-red-800">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
          <p className="text-sm font-semibold">Loading your marketplace inventory...</p>
        </div>
      ) : listings.length === 0 ? (
        <div className="p-16 text-center text-sm text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm italic space-y-3">
          <p>You have not published any marketplace listings yet.</p>
          <button
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-xs shadow-md transition-all"
          >
            + Create First Listing
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((item) => (
            <div key={item.id} className="space-y-3">
              <ListingCard listing={item} />
              <div className="flex items-center justify-end gap-2 px-1">
                <button
                  onClick={() => setEditListing(item)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold border border-blue-200 transition-colors"
                >
                  <Edit3 className="h-3.5 w-3.5" /> Edit
                </button>
                <button
                  onClick={() => setDeleteListing(item)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold border border-red-200 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <ListingFormModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        sellerId={sellerId}
        onSuccess={fetchMyListings}
      />

      {/* Edit Modal */}
      <ListingEditModal
        isOpen={Boolean(editListing)}
        onClose={() => setEditListing(null)}
        listing={editListing}
        actorId={sellerId}
        onSuccess={fetchMyListings}
      />

      {/* Delete Modal */}
      {deleteListing && (
        <DeleteConfirmModal
          isOpen={Boolean(deleteListing)}
          onClose={() => setDeleteListing(null)}
          listingId={deleteListing.id}
          listingTitle={deleteListing.title}
          actorId={sellerId}
          onSuccess={fetchMyListings}
        />
      )}
    </div>
  );
}
