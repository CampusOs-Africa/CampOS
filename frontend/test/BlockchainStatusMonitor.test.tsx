import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BlockchainStatusMonitor } from "../components/verification/BlockchainStatusMonitor";

describe("BlockchainStatusMonitor Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders verified status, transaction hash, and explorer link when fetch succeeds", async () => {
    const mockResponse = {
      user_id: "user-test-01",
      is_verified: true,
      credential_hash: "hash123",
      status: "verified",
      tx_hash: "0xquai_test_hash_01",
      timestamp: "2026-07-30T10:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as any);

    render(
      <BlockchainStatusMonitor
        userId="user-test-01"
        pollingIntervalMs={100000}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Live Quai Network Blockchain Verification")).toBeInTheDocument();
      expect(screen.getByText("Verification Complete")).toBeInTheDocument();
      expect(screen.getByText("Transaction Confirmed")).toBeInTheDocument();
      expect(screen.getByText("0xquai_test_hash_01")).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: /view on quai testnet explorer/i })
      ).toHaveAttribute("href", "https://testnet.quaiscan.io/tx/0xquai_test_hash_01");
    });
  });

  it("renders error state and retry button when fetch fails", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network RPC Failure"));

    render(
      <BlockchainStatusMonitor
        userId="user-test-01"
        pollingIntervalMs={100000}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Connection to Quai RPC Interrupted")).toBeInTheDocument();
      expect(screen.getByText("Network RPC Failure")).toBeInTheDocument();
      expect(screen.getByText("Retry Connection")).toBeInTheDocument();
    });
  });
});
