"use client";

import React, { useState, useEffect } from "react";
import { ListingCard, MarketplaceListingItem } from "../../../components/marketplace/ListingCard";
import { Heart, ArrowLeft, Trash2 } from "lucide-react";
import Link from "next/link";

const WISHLIST_STORAGE_KEY = "campusos_wishlist_items";

export default function WishlistPage() {
  const [items, setItems] = useState<MarketplaceListingItem[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(WISHLIST_STORAGE_KEY);
      if (stored) {
        setItems(JSON.parse(stored));
      }
    } catch (e) {
      // ignore
    }
  }, []);

  const handleClearWishlist = () => {
    localStorage.removeItem(WISHLIST_STORAGE_KEY);
    setItems([]);
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Heart className="h-6 w-6 text-rose-500 fill-rose-500" />
            My Wishlist & Saved Items
          </h1>
          <p className="text-sm text-slate-500">
            Bookmarked items you are interested in buying from Verified Students.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/marketplace"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Marketplace</span>
          </Link>

          {items.length > 0 && (
            <button
              onClick={handleClearWishlist}
              className="inline-flex items-center gap-1 px-4 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold border border-rose-200 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear All</span>
            </button>
          )}
        </div>
      </div>

      {/* Grid */}
      {items.length === 0 ? (
        <div className="p-16 text-center text-sm text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm italic space-y-3">
          <p>Your wishlist is currently empty.</p>
          <Link
            href="/marketplace"
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-xs shadow-md transition-all"
          >
            Explore Marketplace Catalog
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <ListingCard key={item.id} listing={item} />
          ))}
        </div>
      )}
    </div>
  );
}
