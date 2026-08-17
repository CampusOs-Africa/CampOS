"use client";

import React, { useState } from "react";

interface ImageGalleryProps {
  images: string[];
  title: string;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images = [],
  title,
}) => {
  const safeImages =
    images && images.length > 0
      ? images
      : ["https://res.cloudinary.com/demo/image/upload/sample.jpg"];
  const [selectedIdx, setSelectedIdx] = useState(0);

  return (
    <div className="space-y-3">
      {/* Main image */}
      <div className="aspect-[16/10] bg-slate-100 rounded-2xl overflow-hidden border border-slate-200">
        <img
          src={safeImages[selectedIdx] || safeImages[0]}
          alt={title}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Thumbnails */}
      {safeImages.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {safeImages.map((imgUrl, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedIdx(idx)}
              className={`relative aspect-[16/10] w-20 rounded-lg overflow-hidden border-2 transition-all shrink-0 ${
                selectedIdx === idx
                  ? "border-primary-600 ring-2 ring-primary-500/20"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <img src={imgUrl} alt={`${title} thumbnail ${idx + 1}`} className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
