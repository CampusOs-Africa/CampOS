import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TrustLeaderboard } from "../components/trust/TrustLeaderboard";

describe("TrustLeaderboard Component", () => {
  const mockEntries = [
    {
      user_id: "student-1",
      name: "Amina Bello",
      email: "amina@unilag.edu.ng",
      school: "University of Lagos",
      department: "Computer Science",
      trust_score: 92,
      trust_badge: "Platinum",
      is_verified: true,
      rank: 1,
    },
    {
      user_id: "student-2",
      name: "Chidi Okafor",
      email: "chidi@unijos.edu.ng",
      school: "University of Jos",
      department: "Law",
      trust_score: 75,
      trust_badge: "Gold",
      is_verified: true,
      rank: 2,
    },
  ];

  it("renders ranked students with badges and scores", () => {
    render(<TrustLeaderboard entries={mockEntries} />);

    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("Amina Bello")).toBeInTheDocument();
    expect(screen.getByText("92")).toBeInTheDocument();
    expect(screen.getByText("● Platinum")).toBeInTheDocument();

    expect(screen.getByText("#2")).toBeInTheDocument();
    expect(screen.getByText("Chidi Okafor")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
    expect(screen.getByText("● Gold")).toBeInTheDocument();
  });

  it("calls filter callback when institution dropdown changes", () => {
    const handleFilter = vi.fn();
    render(<TrustLeaderboard entries={mockEntries} onFilterChange={handleFilter} />);

    const schoolSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(schoolSelect, { target: { value: "University of Lagos" } });

    expect(handleFilter).toHaveBeenCalledWith("University of Lagos", "all");
  });
});
