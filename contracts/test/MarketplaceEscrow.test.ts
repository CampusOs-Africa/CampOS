import { expect } from "chai";
import { ethers } from "hardhat";
import { MarketplaceEscrow, StudentIdentity } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MarketplaceEscrow Smart Contract (Quai Network)", function () {
  let studentIdentity: StudentIdentity;
  let escrowContract: MarketplaceEscrow;
  let owner: SignerWithAddress;
  let verifiedSeller: SignerWithAddress;
  let unverifiedSeller: SignerWithAddress;
  let buyer: SignerWithAddress;
  let unauthorized: SignerWithAddress;

  const sampleOrderId = ethers.id("order-uuid-test-01");
  const sampleOrderId2 = ethers.id("order-uuid-test-02");
  const sampleOrderId3 = ethers.id("order-uuid-test-03");
  const sampleOrderId4 = ethers.id("order-uuid-test-04");
  const sampleCredHash = ethers.id("seller-cred-hash-01");
  const escrowAmount = ethers.parseEther("1.0"); // 1.0 QUAI

  beforeEach(async function () {
    [owner, verifiedSeller, unverifiedSeller, buyer, unauthorized] =
      await ethers.getSigners();

    // 1. Deploy StudentIdentity
    const StudentIdentityFactory = await ethers.getContractFactory("StudentIdentity");
    studentIdentity = await StudentIdentityFactory.deploy();
    await studentIdentity.waitForDeployment();

    // 2. Register verifiedSeller on StudentIdentity
    await studentIdentity.registerStudent(verifiedSeller.address, sampleCredHash);

    // 3. Deploy MarketplaceEscrow linked to StudentIdentity
    const EscrowFactory = await ethers.getContractFactory("MarketplaceEscrow");
    escrowContract = await EscrowFactory.deploy(await studentIdentity.getAddress());
    await escrowContract.waitForDeployment();
  });

  describe("Deployment & Integration", function () {
    it("Should link to StudentIdentity contract address correctly", async function () {
      expect(await escrowContract.studentIdentity()).to.equal(
        await studentIdentity.getAddress()
      );
    });

    it("Should set the deployer as owner", async function () {
      expect(await escrowContract.owner()).to.equal(owner.address);
    });
  });

  describe("createEscrow() — Verified Student Seller Gating", function () {
    it("Should create escrow successfully when seller is a verified student", async function () {
      await expect(
        escrowContract.createEscrow(
          sampleOrderId,
          buyer.address,
          verifiedSeller.address,
          escrowAmount
        )
      )
        .to.emit(escrowContract, "EscrowCreated")
        .withArgs(sampleOrderId, buyer.address, verifiedSeller.address, escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId);
      expect(esc.buyer).to.equal(buyer.address);
      expect(esc.seller).to.equal(verifiedSeller.address);
      expect(esc.amount).to.equal(escrowAmount);
      expect(esc.state).to.equal(1); // EscrowState.CREATED == 1
    });

    it("Should revert createEscrow when seller is NOT a verified student", async function () {
      await expect(
        escrowContract.createEscrow(
          sampleOrderId,
          buyer.address,
          unverifiedSeller.address,
          escrowAmount
        )
      ).to.be.revertedWith("MarketplaceEscrow: seller must be a verified student");
    });

    it("Should revert when buyer and seller are identical", async function () {
      await expect(
        escrowContract.createEscrow(
          sampleOrderId,
          buyer.address,
          buyer.address,
          escrowAmount
        )
      ).to.be.revertedWith("MarketplaceEscrow: buyer and seller cannot be identical");
    });
  });

  describe("deposit()", function () {
    beforeEach(async function () {
      await escrowContract.createEscrow(
        sampleOrderId,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );
    });

    it("Should allow the buyer to deposit QUAI and transition to FUNDED state", async function () {
      await expect(
        escrowContract.connect(buyer).deposit(sampleOrderId, { value: escrowAmount })
      )
        .to.emit(escrowContract, "EscrowFunded")
        .withArgs(sampleOrderId, escrowAmount, (val: any) => val > 0);

      const esc = await escrowContract.getEscrow(sampleOrderId);
      expect(esc.state).to.equal(2); // EscrowState.FUNDED == 2
      expect(esc.expiresAt).to.be.greaterThan(0);
    });

    it("Should reject incorrect deposit amounts", async function () {
      await expect(
        escrowContract
          .connect(buyer)
          .deposit(sampleOrderId, { value: ethers.parseEther("0.5") })
      ).to.be.revertedWith("MarketplaceEscrow: incorrect deposit amount");
    });
  });

  describe("confirmDelivery()", function () {
    it("Should let the buyer mark delivery (DELIVERED)", async function () {
      await escrowContract.connect(owner).createEscrow(
        sampleOrderId4, buyer.address, verifiedSeller.address, escrowAmount
      );
      await escrowContract.connect(buyer).deposit(sampleOrderId4, { value: escrowAmount });
      await expect(escrowContract.connect(buyer).confirmDelivery(sampleOrderId4))
        .to.emit(escrowContract, "EscrowDelivered");
      const esc = await escrowContract.getEscrow(sampleOrderId4);
      expect(esc.state).to.equal(3); // DELIVERED
    });
  });

  describe("release()", function () {
    beforeEach(async function () {
      await escrowContract.createEscrow(
        sampleOrderId,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );
      await escrowContract.connect(buyer).deposit(sampleOrderId, { value: escrowAmount });
    });

    it("Should release escrowed QUAI to seller and transition to COMPLETED state", async function () {
      const sellerBalanceBefore = await ethers.provider.getBalance(verifiedSeller.address);

      await expect(escrowContract.connect(buyer).release(sampleOrderId))
        .to.emit(escrowContract, "EscrowReleased")
        .withArgs(sampleOrderId, verifiedSeller.address, escrowAmount);

      const sellerBalanceAfter = await ethers.provider.getBalance(verifiedSeller.address);
      expect(sellerBalanceAfter - sellerBalanceBefore).to.equal(escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId);
      expect(esc.state).to.equal(4); // EscrowState.COMPLETED == 4
    });

    it("Should prevent unauthorized accounts from releasing escrow", async function () {
      await expect(
        escrowContract.connect(unauthorized).release(sampleOrderId)
      ).to.be.revertedWith("MarketplaceEscrow: only buyer or admin can release escrow");
    });
  });

  describe("refund()", function () {
    beforeEach(async function () {
      await escrowContract.createEscrow(
        sampleOrderId,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );
      await escrowContract.connect(buyer).deposit(sampleOrderId, { value: escrowAmount });
    });

    it("Should allow seller or admin to refund escrow to buyer and transition to REFUNDED state", async function () {
      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);

      await expect(escrowContract.connect(verifiedSeller).refund(sampleOrderId))
        .to.emit(escrowContract, "EscrowRefunded")
        .withArgs(sampleOrderId, buyer.address, escrowAmount);

      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);
      expect(buyerBalanceAfter - buyerBalanceBefore).to.equal(escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId);
      expect(esc.state).to.equal(5); // EscrowState.REFUNDED == 5
    });
  });

  describe("cancel()", function () {
    it("Should allow buyer or seller to cancel an unfunded escrow", async function () {
      await escrowContract.createEscrow(
        sampleOrderId2,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );

      await expect(escrowContract.connect(buyer).cancel(sampleOrderId2))
        .to.emit(escrowContract, "EscrowCancelled")
        .withArgs(sampleOrderId2);

      const esc = await escrowContract.getEscrow(sampleOrderId2);
      expect(esc.state).to.equal(6); // EscrowState.CANCELLED == 6
    });
  });

  describe("dispute() & resolveDispute()", function () {
    beforeEach(async function () {
      await escrowContract.createEscrow(
        sampleOrderId3,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );
      await escrowContract.connect(buyer).deposit(sampleOrderId3, { value: escrowAmount });
    });

    it("Should allow buyer or seller to dispute a funded escrow", async function () {
      await expect(escrowContract.connect(buyer).dispute(sampleOrderId3))
        .to.emit(escrowContract, "EscrowDisputed")
        .withArgs(sampleOrderId3, buyer.address);

      const esc = await escrowContract.getEscrow(sampleOrderId3);
      expect(esc.state).to.equal(7); // EscrowState.DISPUTED == 7
    });

    it("Should allow owner to resolve a dispute in favor of seller", async function () {
      await escrowContract.connect(buyer).dispute(sampleOrderId3);

      await expect(escrowContract.resolveDispute(sampleOrderId3, true))
        .to.emit(escrowContract, "DisputeResolved")
        .withArgs(sampleOrderId3, true, escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId3);
      expect(esc.state).to.equal(4); // COMPLETED
    });

    it("Should allow owner to resolve a dispute in favor of buyer", async function () {
      await escrowContract.connect(verifiedSeller).dispute(sampleOrderId3);

      await expect(escrowContract.resolveDispute(sampleOrderId3, false))
        .to.emit(escrowContract, "DisputeResolved")
        .withArgs(sampleOrderId3, false, escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId3);
      expect(esc.state).to.equal(5); // REFUNDED
    });
  });

  describe("refundAfterTimeout()", function () {
    it("Should allow buyer to claim refund after escrow timeout duration expires", async function () {
      await escrowContract.createEscrow(
        sampleOrderId4,
        buyer.address,
        verifiedSeller.address,
        escrowAmount
      );
      await escrowContract.connect(buyer).deposit(sampleOrderId4, { value: escrowAmount });

      // Fast-forward EVM timestamp by 15 days (> 14 days defaultTimeoutDuration)
      await ethers.provider.send("evm_increaseTime", [15 * 86400]);
      await ethers.provider.send("evm_mine", []);

      await expect(escrowContract.connect(buyer).refundAfterTimeout(sampleOrderId4))
        .to.emit(escrowContract, "EscrowRefunded")
        .withArgs(sampleOrderId4, buyer.address, escrowAmount);

      const esc = await escrowContract.getEscrow(sampleOrderId4);
      expect(esc.state).to.equal(5); // REFUNDED
    });
  });
});
