"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { PlusCircle, Loader2, CheckCircle2, AlertCircle, X, Image as ImageIcon } from "lucide-react";

interface ListingFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  sellerId: string;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const ListingFormModal: React.FC<ListingFormModalProps> = ({
  isOpen,
  onClose,
  sellerId,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("books");
  const [condition, setCondition] = useState("good");
  const [price, setPrice] = useState("");
  const [imageUrl, setImageUrl] = useState("https://res.cloudinary.com/demo/image/upload/sample.jpg");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const token = typeof window !== "undefined" ? localStorage.getItem("campusos_auth_token") : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsedPrice = parseFloat(price);
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
      setError("Please enter a valid price greater than 0 NGN.");
      return;
    }

    if (!title.trim() || title.length < 3) {
      setError("Title must be at least 3 characters.");
      return;
    }

    if (!description.trim() || description.length < 5) {
      setError("Description must be at least 5 characters.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/marketplace/listings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          seller_id: sellerId,
          title: title.trim(),
          description: description.trim(),
          category: category,
          price: parsedPrice,
          condition: condition,
          inventory_count: 1,
          images: [imageUrl.trim() || "https://res.cloudinary.com/demo/image/upload/sample.jpg"],
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error?.message || data?.detail || "Failed to create listing.");
      }

      // Reset form
      setTitle("");
      setDescription("");
      setPrice("");
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || "Could not publish marketplace listing.");
    } finally {
      setLoading(false);
    }
  };

  const loadSamplePresets = (presetType: string) => {
    switch (presetType) {
      case "book":
        setTitle("Engineering Calculus Volume 1");
        setDescription("Standard university calculus textbook in great condition. Barely used with no highlighted pages.");
        setCategory("books");
        setCondition("like_new");
        setPrice("6500");
        setImageUrl("https://res.cloudinary.com/demo/image/upload/sample.jpg");
        break;
      case "laptop":
        setTitle("MacBook Air M1 8GB/256GB");
        setDescription("Clean laptop used for 1 academic session. Battery health 92%. Comes with original charger.");
        setCategory("electronics");
        setCondition("good");
        setPrice("650000");
        setImageUrl("https://res.cloudinary.com/demo/image/upload/sample.jpg");
        break;
      default:
        break;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
              <PlusCircle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Create Marketplace Listing
              </h3>
              <p className="text-xs text-slate-500">
                Only Verified Students can list items. Protected by Quai Network Escrow.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Demo Preset Buttons */}
        <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200">
          <span className="text-xs font-semibold text-slate-600">
            Quick Fill Demo Item:
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => loadSamplePresets("book")}
              className="px-2.5 py-1 rounded bg-white border border-slate-300 hover:bg-slate-100 text-[11px] font-bold text-slate-700"
            >
              + Calculus Book
            </button>
            <button
              type="button"
              onClick={() => loadSamplePresets("laptop")}
              className="px-2.5 py-1 rounded bg-white border border-slate-300 hover:bg-slate-100 text-[11px] font-bold text-slate-700"
            >
              + MacBook Air
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Engineering Calculus Volume 1"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
              >
                <option value="books">Books</option>
                <option value="electronics">Electronics</option>
                <option value="accommodation">Accommodation</option>
                <option value="tutoring">Tutoring</option>
                <option value="tickets">Tickets</option>
                <option value="services">Services</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Condition
              </label>
              <select
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
              >
                <option value="new">New</option>
                <option value="like_new">Like New</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Price in NGN (₦)
            </label>
            <input
              type="number"
              step="50"
              required
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="5000"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-bold text-slate-900 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Description
            </label>
            <textarea
              rows={3}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe condition, edition, or pickup details..."
              className="w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-900 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Cloudinary Photo URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="url"
                required
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono text-slate-800 focus:border-primary-500 focus:outline-none"
              />
              <ImageIcon className="h-5 w-5 text-slate-400 shrink-0" />
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2 text-xs text-red-800">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Publishing..." : "Publish to Marketplace"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
