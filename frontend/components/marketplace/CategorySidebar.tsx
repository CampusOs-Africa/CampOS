"use client";

import React from "react";
import {
  BookOpen,
  Laptop,
  Home,
  GraduationCap,
  Ticket,
  Wrench,
  LayoutGrid,
  Filter,
  RotateCcw,
} from "lucide-react";

interface CategorySidebarProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  selectedCondition: string;
  onSelectCondition: (condition: string) => void;
  minPrice: string;
  onMinPriceChange: (val: string) => void;
  maxPrice: string;
  onMaxPriceChange: (val: string) => void;
  onApplyFilters: () => void;
  onResetFilters: () => void;
}

export const CategorySidebar: React.FC<CategorySidebarProps> = ({
  selectedCategory,
  onSelectCategory,
  selectedCondition,
  onSelectCondition,
  minPrice,
  onMinPriceChange,
  maxPrice,
  onMaxPriceChange,
  onApplyFilters,
  onResetFilters,
}) => {
  const categories = [
    { id: "all", label: "All Items", icon: LayoutGrid },
    { id: "books", label: "Books & Notes", icon: BookOpen },
    { id: "electronics", label: "Electronics", icon: Laptop },
    { id: "accommodation", label: "Housing", icon: Home },
    { id: "tutoring", label: "Tutoring", icon: GraduationCap },
    { id: "tickets", label: "Event Tickets", icon: Ticket },
    { id: "services", label: "Services", icon: Wrench },
  ];

  const conditionOptions = [
    { id: "all", label: "Any Condition" },
    { id: "new", label: "New" },
    { id: "like_new", label: "Like New" },
    { id: "good", label: "Good" },
    { id: "fair", label: "Fair" },
    { id: "poor", label: "Poor" },
  ];

  return (
    <aside
      className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-6 shrink-0"
      aria-label="Marketplace Filter Sidebar"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-1.5 font-bold text-slate-900 text-sm">
          <Filter className="h-4 w-4 text-primary-600" />
          <span>Filters & Categories</span>
        </div>
        <button
          type="button"
          onClick={onResetFilters}
          className="text-xs text-slate-500 hover:text-primary-600 inline-flex items-center gap-1 transition-colors"
          title="Reset All Filters"
        >
          <RotateCcw className="h-3 w-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Categories */}
      <div className="space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
          Category
        </label>
        <div className="space-y-1">
          {categories.map((cat) => {
            const IconComponent = cat.icon;
            const isSelected = selectedCategory === cat.id;

            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onSelectCategory(cat.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-slate-900 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100/80"
                }`}
                aria-pressed={isSelected}
              >
                <div className="flex items-center gap-2">
                  <IconComponent className="h-4 w-4" />
                  <span>{cat.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Condition Filter */}
      <div className="space-y-2 pt-4 border-t border-slate-100">
        <label
          htmlFor="condition-filter"
          className="block text-xs font-bold uppercase tracking-wider text-slate-400"
        >
          Item Condition
        </label>
        <select
          id="condition-filter"
          value={selectedCondition}
          onChange={(e) => onSelectCondition(e.target.value)}
          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-primary-500 focus:outline-none"
        >
          {conditionOptions.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Price Filter */}
      <div className="space-y-3 pt-4 border-t border-slate-100">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
          Price Range (₦ NGN)
        </label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] text-slate-400 block mb-1">Min</span>
            <input
              type="number"
              step="500"
              placeholder="0"
              value={minPrice}
              onChange={(e) => onMinPriceChange(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:border-primary-500 focus:outline-none"
            />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block mb-1">Max</span>
            <input
              type="number"
              step="500"
              placeholder="Any"
              value={maxPrice}
              onChange={(e) => onMaxPriceChange(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:border-primary-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Quick presets */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <button
            type="button"
            onClick={() => {
              onMinPriceChange("");
              onMaxPriceChange("5000");
              onApplyFilters();
            }}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-[10px] font-bold text-slate-600"
          >
            &lt; ₦5,000
          </button>
          <button
            type="button"
            onClick={() => {
              onMinPriceChange("5000");
              onMaxPriceChange("25000");
              onApplyFilters();
            }}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-[10px] font-bold text-slate-600"
          >
            ₦5k–₦25k
          </button>
          <button
            type="button"
            onClick={() => {
              onMinPriceChange("25000");
              onMaxPriceChange("");
              onApplyFilters();
            }}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-[10px] font-bold text-slate-600"
          >
            &gt; ₦25,000
          </button>
        </div>
      </div>

      {/* Apply Button */}
      <button
        type="button"
        onClick={onApplyFilters}
        className="w-full py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-xs shadow-md transition-all"
      >
        Apply Filter
      </button>
    </aside>
  );
};
