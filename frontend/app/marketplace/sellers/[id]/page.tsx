"use client";
import { API_BASE_URL } from "../../../../lib/api";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { SellerProfileCard } from "../../../../components/marketplace/SellerProfileCard";
import { ListingCard } from "../../../../components/marketplace/ListingCard";
import { ArrowLeft, Loader2, Award, ShieldCheck, ShoppingBag } from "lucide-react";
import Link from "next/link";

export default function SellerProfilePage() {
  const params = useParams();
  const sellerId = params?.id as string;

  const [sellerListings, setSellerListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sellerId) return;
    const fetchSellerListings = async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `${API_BASE_URL}/marketplace/listings?seller_id=${sellerId}`
        );
        if (res.ok) {
          const data = await res.json();
          setSellerListings(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchSellerListings();
  }, [sellerId]);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <Link
        href="/marketplace"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Marketplace Catalog</span>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Col: Full Profile Card */}
        <div>
          <SellerProfileCard sellerId={sellerId} />
        </div>

        {/* Right 2 Cols: Active & Sold Listings by this seller */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border-b border-slate-200 pb-3">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShoppingBag className="h-5 w-5 text-primary-600" />
              <span>Listings by this Seller</span>
            </h2>
          </div>

          {loading ? (
            <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary-600 mb-2" />
              <p className="text-sm font-semibold">Loading seller listings...</p>
            </div>
          ) : sellerListings.length === 0 ? (
            <div className="p-16 text-center text-sm text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm italic">
              This seller currently has no marketplace listings.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {sellerListings.map((item) => (
                <ListingCard key={item.id} listing={item} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
