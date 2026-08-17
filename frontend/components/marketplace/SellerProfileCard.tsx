"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect } from "react";
import { Award, Star, Package, ShoppingBag, ShieldCheck, Loader2 } from "lucide-react";

interface SellerProfileCardProps {
  sellerId: string;
  apiBaseUrl?: string;
}

export const SellerProfileCard: React.FC<SellerProfileCardProps> = ({
  sellerId,
  apiBaseUrl = API_BASE_URL,
}) => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSeller = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiBaseUrl}/marketplace/sellers/${sellerId}`);
        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        }
      } catch (err) {
        // ignore error
      } finally {
        setLoading(false);
      }
    };
    fetchSeller();
  }, [apiBaseUrl, sellerId]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary-600 mb-2" />
        <span className="text-xs">Loading seller reputation profile...</span>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-5">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
        <div className="h-12 w-12 rounded-full bg-primary-100 text-primary-700 font-extrabold flex items-center justify-center text-lg">
          {profile.name ? profile.name[0] : "S"}
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h4 className="font-bold text-slate-900 text-base">{profile.name}</h4>
            {profile.is_verified && (
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
            )}
          </div>
          <p className="text-xs text-slate-500 font-mono truncate">{profile.user_id}</p>
        </div>
      </div>

      {/* Trust Score & Rating Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-center">
          <span className="text-[11px] font-semibold text-amber-700 block uppercase tracking-wider">
            Trust Score
          </span>
          <span className="text-2xl font-extrabold text-amber-900">
            {profile.trust_score}
          </span>
          <span className="text-[10px] text-amber-600 block">0–100 Bounded</span>
        </div>

        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
          <span className="text-[11px] font-semibold text-emerald-700 block uppercase tracking-wider">
            Avg Rating
          </span>
          <div className="flex items-center justify-center gap-1 text-2xl font-extrabold text-emerald-900">
            <span>{profile.average_rating || 5.0}</span>
            <Star className="h-4 w-4 fill-emerald-600 text-emerald-600" />
          </div>
          <span className="text-[10px] text-emerald-600 block">Verified Buyers</span>
        </div>
      </div>

      {/* Active listings & completed sales */}
      <div className="grid grid-cols-2 gap-3 text-xs text-slate-700 border-t border-slate-100 pt-4">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-slate-400" />
          <span>Active Listings: <strong>{profile.active_listings_count}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <ShoppingBag className="h-4 w-4 text-slate-400" />
          <span>Completed Sales: <strong>{profile.total_sales_count}</strong></span>
        </div>
      </div>
    </div>
  );
};
