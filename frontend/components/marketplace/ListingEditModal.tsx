"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect } from "react";
import { Edit3, Loader2, AlertCircle, X, Image as ImageIcon } from "lucide-react";
import { MarketplaceListingItem } from "./ListingCard";

interface ListingEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  listing: MarketplaceListingItem | null;
  actorId: string;
  apiBaseUrl?: string;
  onSuccess?: () => void;
}

export const ListingEditModal: React.FC<ListingEditModalProps> = ({
  isOpen,
  onClose,
  listing,
  actorId,
  apiBaseUrl = API_BASE_URL,
  onSuccess,
}) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("books");
  const [condition, setCondition] = useState("good");
  const [price, setPrice] = useState("");
  const [inventoryCount, setInventoryCount] = useState("1");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (listing) {
      setTitle(listing.title || "");
      setDescription(listing.description || "");
      setCategory(listing.category || "books");
      setCondition(listing.condition || "good");
      setPrice(listing.price ? listing.price.toString() : "");
      setInventoryCount(
        listing.inventory_count ? listing.inventory_count.toString() : "1"
      );
      setImageUrl(
        listing.images && listing.images.length > 0 ? listing.images[0] : ""
      );
    }
  }, [listing]);

  if (!isOpen || !listing) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsedPrice = parseFloat(price);
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
      setError("Please enter a valid price greater than 0 NGN.");
      return;
    }

    const parsedInventory = parseInt(inventoryCount, 10);
    if (isNaN(parsedInventory) || parsedInventory < 0) {
      setError("Please enter a valid inventory count (0 or higher).");
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
      const res = await fetch(
        `${apiBaseUrl}/marketplace/listings/${listing.id}?actor_id=${actorId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title.trim(),
            description: description.trim(),
            category: category,
            price: parsedPrice,
            condition: condition,
            inventory_count: parsedInventory,
            images: [
              imageUrl.trim() ||
                "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            ],
          }),
        }
      );

      const data = await res.json();
      if (!res.ok) {
        throw new Error(
          data?.error?.message || data?.detail || "Failed to update listing."
        );
      }

      if (onSuccess) {
        onSuccess();
      }
      onClose();
    } catch (err: any) {
      setError(err.message || "Could not update marketplace listing.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-listing-modal-title"
    >
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Edit3 className="h-6 w-6" />
            </div>
            <div>
              <h3
                id="edit-listing-modal-title"
                className="text-lg font-bold text-slate-900"
              >
                Edit Marketplace Listing
              </h3>
              <p className="text-xs text-slate-500">
                Update item details, price, condition & inventory.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition-colors"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="edit-title"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
            >
              Title
            </label>
            <input
              id="edit-title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Engineering Calculus Volume 1"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="edit-category"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
              >
                Category
              </label>
              <select
                id="edit-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
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
              <label
                htmlFor="edit-condition"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
              >
                Condition
              </label>
              <select
                id="edit-condition"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="new">New</option>
                <option value="like_new">Like New</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="edit-price"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
              >
                Price in NGN (₦)
              </label>
              <input
                id="edit-price"
                type="number"
                step="50"
                required
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-bold text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            <div>
              <label
                htmlFor="edit-inventory"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
              >
                Inventory Count
              </label>
              <input
                id="edit-inventory"
                type="number"
                required
                min="0"
                max="100"
                value={inventoryCount}
                onChange={(e) => setInventoryCount(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-bold text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="edit-description"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
            >
              Description
            </label>
            <textarea
              id="edit-description"
              rows={3}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          <div>
            <label
              htmlFor="edit-image"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1"
            >
              Cloudinary Photo URL
            </label>
            <div className="flex items-center gap-2">
              <input
                id="edit-image"
                type="url"
                required
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono text-slate-800 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <ImageIcon className="h-5 w-5 text-slate-400 shrink-0" />
            </div>
          </div>

          {error && (
            <div
              className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2 text-xs text-red-800"
              role="alert"
            >
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white shadow-lg transition-all disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
