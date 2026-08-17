import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("Starting Quai Network deployment for StudentIdentity...");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "QUAI");

  const StudentIdentityFactory = await ethers.getContractFactory("StudentIdentity");
  const studentIdentity = await StudentIdentityFactory.deploy();

  await studentIdentity.waitForDeployment();

  const contractAddress = await studentIdentity.getAddress();
  const deployTx = studentIdentity.deploymentTransaction();

  console.log("==================================================");
  console.log("StudentIdentity deployed successfully!");
  console.log("Contract Address:", contractAddress);
  console.log("Transaction Hash:", deployTx?.hash || "N/A");
  console.log("==================================================");

  // Save ABI and deployment metadata for backend integration
  const artifactPath = path.join(__dirname, "../artifacts/contracts/StudentIdentity.sol/StudentIdentity.json");
  if (fs.existsSync(artifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    const deploymentData = {
      address: contractAddress,
      tx_hash: deployTx?.hash || "",
      network: "orchard",
      deployedAt: new Date().toISOString(),
      abi: artifact.abi,
    };

    const abiOutputDir = path.join(__dirname, "../abi");
    if (!fs.existsSync(abiOutputDir)) {
      fs.mkdirSync(abiOutputDir, { recursive: true });
    }
    fs.writeFileSync(
      path.join(abiOutputDir, "StudentIdentityDeployment.json"),
      JSON.stringify(deploymentData, null, 2)
    );
    console.log("Deployment metadata saved to abi/StudentIdentityDeployment.json");

    // Also copy ABI to backend app/contracts directory
    const backendAbiDir = path.join(__dirname, "../../backend/app/contracts");
    if (fs.existsSync(backendAbiDir)) {
      fs.writeFileSync(
        path.join(backendAbiDir, "student_identity_abi.json"),
        JSON.stringify(artifact.abi, null, 2)
      );
      console.log("ABI copied to backend/app/contracts/student_identity_abi.json");
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
