import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ListingCard } from "../components/marketplace/ListingCard";

describe("ListingCard Component", () => {
  it("renders title, price, condition badge, seller name, and trust score", () => {
    const sampleListing = {
      id: "listing-test-01",
      seller_id: "seller-01",
      title: "Engineering Calculus Volume 1",
      description: "Great textbook",
      category: "books",
      price: 6500,
      condition: "like_new",
      images: ["https://res.cloudinary.com/test/calc.jpg"],
      status: "active",
      inventory_count: 1,
      created_at: "2026-07-30T10:00:00Z",
      seller_name: "Amina Bello",
      seller_trust_score: 75,
      seller_verified: true,
    };

    render(<ListingCard listing={sampleListing} />);

    expect(screen.getByText("Engineering Calculus Volume 1")).toBeInTheDocument();
    expect(screen.getByText("like new")).toBeInTheDocument();
    expect(screen.getByText("₦6,500")).toBeInTheDocument();
    expect(screen.getByText("Amina Bello")).toBeInTheDocument();
    expect(screen.getByText("Trust Score: 75")).toBeInTheDocument();
  });
});
