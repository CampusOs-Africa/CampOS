import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CampusIdentityQR } from "../components/identity/CampusIdentityQR";

describe("CampusIdentityQR Component", () => {
  it("renders student UUID, verification status, credential ID, timestamp, and signature", () => {
    render(
      <CampusIdentityQR
        userId="student-uuid-test-999"
        status="verified"
        credentialId="0xquai_cred_hash_test_777"
        timestamp="2026-07-30T10:00:00Z"
        signature="hmac_sha256_sig_test_888"
      />
    );

    expect(screen.getByText("Campus Identity QR Credential")).toBeInTheDocument();
    expect(screen.getByText("student-uuid-test-999")).toBeInTheDocument();
    expect(screen.getByText("0xquai_cred_hash_test_777")).toBeInTheDocument();
    expect(screen.getByText("hmac_sha256_sig_test_888")).toBeInTheDocument();
    expect(screen.getByText("Verified Student")).toBeInTheDocument();
  });
});
