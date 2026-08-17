"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect, useCallback } from "react";
import { ListingCard, MarketplaceListingItem } from "./ListingCard";
import { CategoryCards } from "./CategoryCards";
import { Search, Filter, Loader2, PlusCircle, RefreshCw } from "lucide-react";

interface ListingGridProps {
  apiBaseUrl?: string;
  onCreateClick?: () => void;
}

export const ListingGrid: React.FC<ListingGridProps> = ({
  apiBaseUrl = API_BASE_URL,
  onCreateClick,
}) => {
  const [listings, setListings] = useState<MarketplaceListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<string>("all");
  const [condition, setCondition] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");

  const fetchListings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (category !== "all") params.append("category", category);
      if (condition !== "all") params.append("condition", condition);
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      if (minPrice.trim() && !isNaN(parseFloat(minPrice))) {
        params.append("min_price", minPrice.trim());
      }
      if (maxPrice.trim() && !isNaN(parseFloat(maxPrice))) {
        params.append("max_price", maxPrice.trim());
      }

      const res = await fetch(`${apiBaseUrl}/marketplace/listings?${params.toString()}`);
      if (!res.ok) {
        throw new Error("Failed to load marketplace listings.");
      }
      const data = await res.json();
      setListings(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || "Error fetching marketplace items.");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, category, condition, minPrice, maxPrice, searchQuery]);

  useEffect(() => {
    fetchListings();
  }, [fetchListings]);

  return (
    <div className="space-y-6">
      {/* Category Visual Cards */}
      <CategoryCards selectedCategory={category} onSelectCategory={setCategory} />

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search books, laptops, housing..."
              className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none"
            />
          </div>

          {/* Price Range, Condition selector & Reload */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500 font-semibold">Min ₦:</span>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="0"
                className="w-16 bg-transparent text-xs font-bold text-slate-800 focus:outline-none"
              />
              <span className="text-xs text-slate-500 font-semibold">Max ₦:</span>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="Any"
                className="w-16 bg-transparent text-xs font-bold text-slate-800 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
              <Filter className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-xs text-slate-500 font-semibold">Condition:</span>
              <select
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="bg-transparent text-xs font-bold text-slate-800 focus:outline-none"
              >
                <option value="all">Any</option>
                <option value="new">New</option>
                <option value="like_new">Like New</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
              </select>
            </div>

            <button
              type="button"
              onClick={fetchListings}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
              title="Refresh Listings"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            {onCreateClick && (
              <button
                type="button"
                onClick={onCreateClick}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-bold text-white shadow-sm transition-all"
              >
                <PlusCircle className="h-4 w-4" />
                <span>+ List Item</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Bar */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 font-semibold" role="alert">
          {error}
        </div>
      )}

      {/* Grid Content */}
      {loading ? (
        <div className="p-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
          <p className="text-sm font-semibold">Loading marketplace listings...</p>
        </div>
      ) : listings.length === 0 ? (
        <div className="p-16 text-center text-sm text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm italic">
          No marketplace listings found matching your search and category filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((item) => (
            <ListingCard key={item.id} listing={item} />
          ))}
        </div>
      )}
    </div>
  );
};
