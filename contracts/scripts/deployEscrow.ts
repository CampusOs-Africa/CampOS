import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("Starting Quai Network deployment for StudentIdentity & MarketplaceEscrow...");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "QUAI");

  // 1. Deploy StudentIdentity
  const StudentIdentityFactory = await ethers.getContractFactory("StudentIdentity");
  const studentIdentity = await StudentIdentityFactory.deploy();
  await studentIdentity.waitForDeployment();

  const identityAddress = await studentIdentity.getAddress();
  const identityTx = studentIdentity.deploymentTransaction();

  console.log("==================================================");
  console.log("1. StudentIdentity deployed successfully!");
  console.log("   Contract Address:", identityAddress);
  console.log("   Transaction Hash:", identityTx?.hash || "N/A");

  // 2. Deploy MarketplaceEscrow (linked to StudentIdentity)
  const MarketplaceEscrowFactory = await ethers.getContractFactory("MarketplaceEscrow");
  const marketplaceEscrow = await MarketplaceEscrowFactory.deploy(identityAddress);
  await marketplaceEscrow.waitForDeployment();

  const escrowAddress = await marketplaceEscrow.getAddress();
  const escrowTx = marketplaceEscrow.deploymentTransaction();

  console.log("==================================================");
  console.log("2. MarketplaceEscrow deployed successfully!");
  console.log("   Contract Address:", escrowAddress);
  console.log("   Transaction Hash:", escrowTx?.hash || "N/A");
  console.log("   Linked StudentIdentity:", identityAddress);
  console.log("==================================================");

  // 3. Save ABIs and deployment metadata for backend integration
  const abiOutputDir = path.join(__dirname, "../abi");
  const backendAbiDir = path.join(__dirname, "../../backend/app/contracts");

  if (!fs.existsSync(abiOutputDir)) {
    fs.mkdirSync(abiOutputDir, { recursive: true });
  }
  if (!fs.existsSync(backendAbiDir)) {
    fs.mkdirSync(backendAbiDir, { recursive: true });
  }

  // Save StudentIdentity ABI & Deployment
  const identityArtifactPath = path.join(
    __dirname,
    "../artifacts/contracts/StudentIdentity.sol/StudentIdentity.json"
  );
  if (fs.existsSync(identityArtifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(identityArtifactPath, "utf8"));
    fs.writeFileSync(
      path.join(abiOutputDir, "StudentIdentity.json"),
      JSON.stringify(artifact.abi, null, 2)
    );
    fs.writeFileSync(
      path.join(abiOutputDir, "StudentIdentityDeployment.json"),
      JSON.stringify(
        {
          address: identityAddress,
          tx_hash: identityTx?.hash || "",
          network: "orchard",
          deployedAt: new Date().toISOString(),
          abi: artifact.abi,
        },
        null,
        2
      )
    );
    fs.writeFileSync(
      path.join(backendAbiDir, "student_identity_abi.json"),
      JSON.stringify(artifact.abi, null, 2)
    );
  }

  // Save MarketplaceEscrow ABI & Deployment
  const escrowArtifactPath = path.join(
    __dirname,
    "../artifacts/contracts/MarketplaceEscrow.sol/MarketplaceEscrow.json"
  );
  if (fs.existsSync(escrowArtifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(escrowArtifactPath, "utf8"));
    fs.writeFileSync(
      path.join(abiOutputDir, "MarketplaceEscrow.json"),
      JSON.stringify(artifact.abi, null, 2)
    );
    fs.writeFileSync(
      path.join(abiOutputDir, "MarketplaceEscrowDeployment.json"),
      JSON.stringify(
        {
          address: escrowAddress,
          studentIdentityAddress: identityAddress,
          tx_hash: escrowTx?.hash || "",
          network: "orchard",
          deployedAt: new Date().toISOString(),
          abi: artifact.abi,
        },
        null,
        2
      )
    );
    fs.writeFileSync(
      path.join(backendAbiDir, "marketplace_escrow_abi.json"),
      JSON.stringify(artifact.abi, null, 2)
    );
    console.log("ABIs and deployment metadata saved to abi/ and backend/app/contracts/!");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
