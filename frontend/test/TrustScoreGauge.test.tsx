import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TrustScoreGauge } from "../components/trust/TrustScoreGauge";

describe("TrustScoreGauge Component", () => {
  const mockData = {
    user_id: "user-test-01",
    name: "Amina Bello",
    email: "amina@unijos.edu.ng",
    verification_status: "verified",
    trust_score: 88,
    trust_badge: "Platinum",
    total_positive_earned: 40,
    total_penalties_deducted: 2,
    completed_sales: 6,
    peer_reviews_count: 3,
    average_rating: 4.8,
  };

  it("renders bounded trust score and tier badge correctly", () => {
    render(<TrustScoreGauge data={mockData} />);

    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText(/● Platinum Tier/i)).toBeInTheDocument();
    expect(screen.getByText("Out of 100")).toBeInTheDocument();
  });

  it("displays positive earned, penalties deducted, sales, and reviews counters", () => {
    render(<TrustScoreGauge data={mockData} />);

    expect(screen.getByText("+40")).toBeInTheDocument();
    expect(screen.getByText("-2")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText(/4.8★/i)).toBeInTheDocument();
  });
});
