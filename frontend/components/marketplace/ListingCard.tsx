"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Award, ArrowRight } from "lucide-react";
import { VerificationBadge } from "../verification/VerificationBadge";
import { WishlistButton } from "./WishlistButton";

export interface MarketplaceListingItem {
  id: string;
  seller_id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  condition: string;
  images: string[];
  status: string;
  inventory_count: number;
  created_at: string;
  seller_name?: string | null;
  seller_trust_score?: number | null;
  seller_verified?: boolean | null;
}

interface ListingCardProps {
  listing: MarketplaceListingItem;
}

export const ListingCard: React.FC<ListingCardProps> = React.memo(({ listing }) => {
  const coverImage =
    listing.images && listing.images.length > 0
      ? listing.images[0]
      : "https://res.cloudinary.com/demo/image/upload/sample.jpg";

  const getConditionBadge = (cond: string) => {
    switch (cond.toLowerCase()) {
      case "new":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "like_new":
        return "bg-blue-50 text-blue-700 border-blue-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="group bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden flex flex-col justify-between">
      <div>
        {/* Cover Image & Category/Condition/Wishlist Chip */}
        <div className="relative aspect-[16/10] bg-slate-100 overflow-hidden">
          <img
            src={coverImage}
            alt={listing.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute top-3 left-3 flex items-center gap-1.5">
            <span className="px-2.5 py-1 rounded-full bg-slate-900/80 backdrop-blur-sm text-white text-[11px] font-bold uppercase tracking-wider">
              {listing.category}
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border uppercase ${getConditionBadge(
                listing.condition
              )}`}
            >
              {listing.condition.replace("_", " ")}
            </span>
          </div>

          <div className="absolute top-3 right-3">
            <WishlistButton listing={listing} />
          </div>

          {listing.status !== "active" && (
            <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-[2px] flex items-center justify-center">
              <span className="px-4 py-1.5 rounded-full bg-red-600 text-white text-xs font-extrabold uppercase tracking-widest shadow-lg">
                {listing.status}
              </span>
            </div>
          )}
        </div>

        {/* Title & Description */}
        <div className="p-5 space-y-2">
          <h3 className="font-bold text-slate-900 text-base line-clamp-1 group-hover:text-primary-600 transition-colors">
            {listing.title}
          </h3>
          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
            {listing.description}
          </p>
        </div>
      </div>

      {/* Footer: Seller trust & Price */}
      <div className="px-5 pb-5 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-700 truncate max-w-[110px]">
              {listing.seller_name || "Verified Student"}
            </span>
            {listing.seller_verified && (
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
            )}
          </div>
          <div className="flex items-center gap-1 text-[11px] font-bold text-amber-600">
            <Award className="h-3 w-3" />
            <span>Trust Score: {listing.seller_trust_score ?? 60}</span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-lg font-extrabold text-slate-900">
            ₦{listing.price.toLocaleString("en-NG", { minimumFractionDigits: 0 })}
          </div>
          <Link
            href={`/marketplace/${listing.id}`}
            className="inline-flex items-center gap-1 text-xs font-bold text-primary-600 hover:text-primary-500 transition-colors"
          >
            <span>View & Buy</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>
    </div>
  );
});

ListingCard.displayName = "ListingCard";
