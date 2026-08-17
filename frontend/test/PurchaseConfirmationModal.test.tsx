import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PurchaseConfirmationModal } from "../components/marketplace/PurchaseConfirmationModal";

describe("PurchaseConfirmationModal Component", () => {
  it("renders order confirmation, Blip Pay reference, and Quai Escrow Tx Hash", () => {
    const sampleOrder = {
      id: "order-test-uuid-999",
      payment_reference: "blip_ref_sample_01",
      escrow_tx_hash: "0xquai_escrow_lock_test_hash",
      amount: 6500,
      listing_title: "Engineering Calculus Volume 1",
    };

    render(
      <PurchaseConfirmationModal
        isOpen={true}
        onClose={() => {}}
        order={sampleOrder}
      />
    );

    expect(screen.getByText("Order Confirmed & Quai Escrow Locked!")).toBeInTheDocument();
    expect(screen.getByText("Engineering Calculus Volume 1")).toBeInTheDocument();
    expect(screen.getByText("₦6,500")).toBeInTheDocument();
    expect(screen.getByText("order-test-uuid-999")).toBeInTheDocument();
    expect(screen.getByText("blip_ref_sample_01")).toBeInTheDocument();
    expect(screen.getByText("0xquai_escrow_lock_test_hash")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /quai explorer/i })
    ).toHaveAttribute(
      "href",
      "https://testnet.quaiscan.io/tx/0xquai_escrow_lock_test_hash"
    );
  });
});
