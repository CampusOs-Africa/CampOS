"use client";

import React, { useState, useEffect } from "react";
import { Heart } from "lucide-react";
import { MarketplaceListingItem } from "./ListingCard";

interface WishlistButtonProps {
  listing: MarketplaceListingItem;
  className?: string;
}

const WISHLIST_STORAGE_KEY = "campusos_wishlist_items";

export const WishlistButton: React.FC<WishlistButtonProps> = ({
  listing,
  className = "",
}) => {
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(WISHLIST_STORAGE_KEY);
      if (stored) {
        const items: MarketplaceListingItem[] = JSON.parse(stored);
        setIsSaved(items.some((item) => item.id === listing.id));
      }
    } catch (e) {
      // ignore storage errors
    }
  }, [listing.id]);

  const toggleWishlist = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    try {
      const stored = localStorage.getItem(WISHLIST_STORAGE_KEY);
      let items: MarketplaceListingItem[] = stored ? JSON.parse(stored) : [];

      if (isSaved) {
        items = items.filter((item) => item.id !== listing.id);
        setIsSaved(false);
      } else {
        items.push(listing);
        setIsSaved(true);
      }
      localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(items));
    } catch (err) {
      // ignore storage error
    }
  };

  return (
    <button
      type="button"
      onClick={toggleWishlist}
      className={`p-2 rounded-full bg-white/80 hover:bg-white backdrop-blur-sm transition-all shadow-sm ${
        isSaved ? "text-rose-500" : "text-slate-400 hover:text-rose-500"
      } ${className}`}
      aria-label={isSaved ? "Remove from wishlist" : "Save to wishlist"}
      title={isSaved ? "Saved in Wishlist" : "Add to Wishlist"}
    >
      <Heart className={`h-4 w-4 ${isSaved ? "fill-rose-500" : ""}`} />
    </button>
  );
};
