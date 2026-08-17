import { expect } from "chai";
import { ethers } from "hardhat";
import { StudentIdentity } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("StudentIdentity Smart Contract (Quai Network)", function () {
  let studentIdentity: StudentIdentity;
  let owner: SignerWithAddress;
  let student1: SignerWithAddress;
  let student2: SignerWithAddress;
  let unauthorized: SignerWithAddress;

  // Sample SHA-256 credential hash (32 bytes / bytes32)
  const sampleHash1 = ethers.id("user-101|amina.bello@unijos.edu.ng|https://res.cloudinary.com/id1.pdf");
  const sampleHash2 = ethers.id("user-102|chidi.okafor@unijos.edu.ng|https://res.cloudinary.com/id2.pdf");

  beforeEach(async function () {
    [owner, student1, student2, unauthorized] = await ethers.getSigners();

    const StudentIdentityFactory = await ethers.getContractFactory("StudentIdentity");
    studentIdentity = await StudentIdentityFactory.deploy();
    await studentIdentity.waitForDeployment();
  });

  describe("Deployment & Initial State", function () {
    it("Should set the deployer as the contract owner", async function () {
      expect(await studentIdentity.owner()).to.equal(owner.address);
    });

    it("Should return false for unverified students initially", async function () {
      expect(await studentIdentity.isVerified(student1.address)).to.be.false;
      expect(await studentIdentity.getCredentialHash(student1.address)).to.equal(ethers.ZeroHash);
    });
  });

  describe("Student Registration & Verification", function () {
    it("Should allow the owner to register a student with a SHA-256 credential hash", async function () {
      await expect(studentIdentity.registerStudent(student1.address, sampleHash1))
        .to.emit(studentIdentity, "StudentRegistered")
        .withArgs(student1.address, sampleHash1, (val: any) => val > 0);

      expect(await studentIdentity.isVerified(student1.address)).to.be.true;
      expect(await studentIdentity.getCredentialHash(student1.address)).to.equal(sampleHash1);
    });

    it("Should reject zero addresses or zero hashes", async function () {
      await expect(
        studentIdentity.registerStudent(ethers.ZeroAddress, sampleHash1)
      ).to.be.revertedWith("StudentIdentity: zero address invalid");

      await expect(
        studentIdentity.registerStudent(student1.address, ethers.ZeroHash)
      ).to.be.revertedWith("StudentIdentity: empty credential hash invalid");
    });

    it("Should allow the owner to re-verify a registered student", async function () {
      await studentIdentity.registerStudent(student1.address, sampleHash1);
      
      await expect(studentIdentity.verifyStudent(student1.address))
        .to.emit(studentIdentity, "StudentVerified")
        .withArgs(student1.address, (val: any) => val > 0);

      expect(await studentIdentity.isVerified(student1.address)).to.be.true;
    });

    it("Should revert verifyStudent if the student was never registered", async function () {
      await expect(studentIdentity.verifyStudent(student2.address)).to.be.revertedWith(
        "StudentIdentity: student not registered"
      );
    });
  });

  describe("Revocation", function () {
    it("Should allow the owner to revoke a student's verified status", async function () {
      await studentIdentity.registerStudent(student1.address, sampleHash1);
      expect(await studentIdentity.isVerified(student1.address)).to.be.true;

      await expect(studentIdentity.revokeStudent(student1.address))
        .to.emit(studentIdentity, "StudentRevoked")
        .withArgs(student1.address, (val: any) => val > 0);

      expect(await studentIdentity.isVerified(student1.address)).to.be.false;
      // Credential hash should remain intact for auditability
      expect(await studentIdentity.getCredentialHash(student1.address)).to.equal(sampleHash1);
    });
  });

  describe("Access Control (onlyOwner)", function () {
    it("Should prevent unauthorized accounts from calling administrative functions", async function () {
      await expect(
        studentIdentity.connect(unauthorized).registerStudent(student1.address, sampleHash1)
      ).to.be.revertedWith("StudentIdentity: caller is not the owner");

      await expect(
        studentIdentity.connect(unauthorized).verifyStudent(student1.address)
      ).to.be.revertedWith("StudentIdentity: caller is not the owner");

      await expect(
        studentIdentity.connect(unauthorized).revokeStudent(student1.address)
      ).to.be.revertedWith("StudentIdentity: caller is not the owner");
    });
  });
});
