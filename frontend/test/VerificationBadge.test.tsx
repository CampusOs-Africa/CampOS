import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { VerificationBadge } from "../components/verification/VerificationBadge";

describe("VerificationBadge Component", () => {
  it("renders verified status correctly", () => {
    render(<VerificationBadge status="verified" />);
    expect(screen.getByText("Verified Student")).toBeInTheDocument();
  });

  it("renders pending status correctly", () => {
    render(<VerificationBadge status="pending" />);
    expect(screen.getByText("Pending Verification")).toBeInTheDocument();
  });

  it("renders rejected status correctly", () => {
    render(<VerificationBadge status="rejected" />);
    expect(screen.getByText("Rejected")).toBeInTheDocument();
  });

  it("renders resubmission needed status correctly", () => {
    render(<VerificationBadge status="resubmission_requested" />);
    expect(screen.getByText("Resubmission Needed")).toBeInTheDocument();
  });
});
