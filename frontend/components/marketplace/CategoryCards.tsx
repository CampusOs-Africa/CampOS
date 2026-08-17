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
} from "lucide-react";

interface CategoryCardsProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

export const CategoryCards: React.FC<CategoryCardsProps> = React.memo(({
  selectedCategory,
  onSelectCategory,
}) => {
  const categories = [
    {
      id: "all",
      label: "All Items",
      description: "Browse everything",
      icon: LayoutGrid,
      color: "bg-slate-900 text-white",
      hover: "hover:bg-slate-800",
    },
    {
      id: "books",
      label: "Books & Notes",
      description: "Textbooks & past questions",
      icon: BookOpen,
      color: "bg-amber-50 text-amber-700 border-amber-200",
      hover: "hover:bg-amber-100/80",
    },
    {
      id: "electronics",
      label: "Electronics",
      description: "Laptops, phones & gadgets",
      icon: Laptop,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      hover: "hover:bg-blue-100/80",
    },
    {
      id: "accommodation",
      label: "Housing",
      description: "Hostels & room shares",
      icon: Home,
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
      hover: "hover:bg-emerald-100/80",
    },
    {
      id: "tutoring",
      label: "Tutoring",
      description: "Academic coaching & lessons",
      icon: GraduationCap,
      color: "bg-purple-50 text-purple-700 border-purple-200",
      hover: "hover:bg-purple-100/80",
    },
    {
      id: "tickets",
      label: "Event Tickets",
      description: "Campus shows & NFT passes",
      icon: Ticket,
      color: "bg-rose-50 text-rose-700 border-rose-200",
      hover: "hover:bg-rose-100/80",
    },
    {
      id: "services",
      label: "Services",
      description: "Laundry, repairs & design",
      icon: Wrench,
      color: "bg-cyan-50 text-cyan-700 border-cyan-200",
      hover: "hover:bg-cyan-100/80",
    },
  ];

  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3"
      role="group"
      aria-label="Marketplace Categories"
    >
      {categories.map((cat) => {
        const IconComponent = cat.icon;
        const isSelected = selectedCategory === cat.id;

        return (
          <button
            key={cat.id}
            type="button"
            onClick={() => onSelectCategory(cat.id)}
            className={`flex flex-col items-start justify-between p-3.5 rounded-2xl border transition-all text-left group focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              isSelected
                ? "bg-slate-900 text-white border-slate-900 shadow-md ring-2 ring-primary-500/30"
                : `bg-white text-slate-800 border-slate-200 hover:border-slate-300 hover:shadow-sm ${cat.hover}`
            }`}
            aria-pressed={isSelected}
          >
            <div
              className={`p-2 rounded-xl transition-colors ${
                isSelected
                  ? "bg-white/10 text-white"
                  : "bg-slate-100 text-slate-700 group-hover:bg-slate-200/80"
              }`}
            >
              <IconComponent className="h-5 w-5" />
            </div>

            <div className="mt-3">
              <span className="block text-xs font-bold truncate">
                {cat.label}
              </span>
              <span
                className={`block text-[10px] truncate mt-0.5 ${
                  isSelected ? "text-slate-300" : "text-slate-500"
                }`}
              >
                {cat.description}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
});

CategoryCards.displayName = "CategoryCards";
