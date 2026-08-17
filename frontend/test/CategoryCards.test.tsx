import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CategoryCards } from "../components/marketplace/CategoryCards";

describe("CategoryCards Component", () => {
  it("renders all 7 category cards and triggers selection callback", () => {
    const handleSelect = vi.fn();
    render(
      <CategoryCards
        selectedCategory="all"
        onSelectCategory={handleSelect}
      />
    );

    expect(screen.getByText("All Items")).toBeInTheDocument();
    expect(screen.getByText("Books & Notes")).toBeInTheDocument();
    expect(screen.getByText("Electronics")).toBeInTheDocument();
    expect(screen.getByText("Housing")).toBeInTheDocument();
    expect(screen.getByText("Tutoring")).toBeInTheDocument();
    expect(screen.getByText("Event Tickets")).toBeInTheDocument();
    expect(screen.getByText("Services")).toBeInTheDocument();

    const electronicsBtn = screen.getByText("Electronics").closest("button");
    if (electronicsBtn) {
      fireEvent.click(electronicsBtn);
    }
    expect(handleSelect).toHaveBeenCalledWith("electronics");
  });
});
