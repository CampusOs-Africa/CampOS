/**
 * Quai-native deployment using the Quais SDK, for either Orchard Testnet
 * (Cyprus-1) or Quai Mainnet (Cyprus-1) — selected by QUAI_TARGET_NETWORK.
 *
 * Usage:
 *   # Testnet (default)
 *   QUAI_TARGET_NETWORK=testnet QUAI_TESTNET_PRIVATE_KEY=<hex> \
 *     npx hardhat run scripts/deployQuai.ts
 *
 *   # Mainnet — requires explicit confirmation, see CONFIRM_MAINNET_DEPLOY below
 *   QUAI_TARGET_NETWORK=mainnet QUAI_MAINNET_PRIVATE_KEY=<hex> \
 *     CONFIRM_MAINNET_DEPLOY=yes npx hardhat run scripts/deployQuai.ts
 *
 * The deployer key must be funded on the target network's Cyprus-1 zone and
 * correspond to an address in that zone. Unlike standard Hardhat/Ethers, Quai
 * requires zone-aware address derivation, which the Quais wallet handles.
 */
import { quais } from "quais";
import * as fs from "fs";
import * as path from "path";

const TARGET = (process.env.QUAI_TARGET_NETWORK || "testnet").toLowerCase();
const IS_MAINNET = TARGET === "mainnet";

const RPC_URL = IS_MAINNET
  ? process.env.QUAI_MAINNET_RPC_URL || "https://rpc.quai.network/cyprus1"
  : process.env.QUAI_TESTNET_RPC_URL || "https://orchard.rpc.quai.network/cyprus1";

const CHAIN_ID = Number(
  IS_MAINNET
    ? process.env.QUAI_MAINNET_CHAIN_ID || 9
    : process.env.QUAI_TESTNET_CHAIN_ID || 15000
);

const PRIVATE_KEY = IS_MAINNET
  ? process.env.QUAI_MAINNET_PRIVATE_KEY
  : process.env.QUAI_TESTNET_PRIVATE_KEY;

async function main() {
  if (!PRIVATE_KEY) {
    throw new Error(
      `${IS_MAINNET ? "QUAI_MAINNET_PRIVATE_KEY" : "QUAI_TESTNET_PRIVATE_KEY"} is required for ${TARGET} deployment`
    );
  }
  // Mainnet deploys real, spendable QUAI on gas — require an explicit,
  // separate confirmation flag so this never fires by an env-var typo.
  if (IS_MAINNET && process.env.CONFIRM_MAINNET_DEPLOY !== "yes") {
    throw new Error(
      "Refusing to deploy to Quai Mainnet without CONFIRM_MAINNET_DEPLOY=yes. " +
        "This deploys with real QUAI — set that flag only when you mean it."
    );
  }

  const provider = new quais.JsonRpcProvider(RPC_URL);
  const wallet = new quais.Wallet(PRIVATE_KEY, provider);
  console.log(`Target network: ${TARGET} (chainId ${CHAIN_ID})`);
  console.log("Deployer:", wallet.address);

  const balance = await provider.getBalance(wallet.address);
  console.log("Balance:", quais.formatQuai(balance), "QUAI");
  if (balance === 0n) {
    throw new Error(
      IS_MAINNET
        ? "Deployer balance is 0 QUAI on mainnet — fund the address before deploying."
        : "Deployer balance is 0 QUAI on testnet — fund it from https://orchard.faucet.quai.network/"
    );
  }

  // ABIs + compiled bytecode are read from Hardhat artifacts.
  const readArtifact = (name: string) => {
    const p = path.join(__dirname, "..", "artifacts", "contracts", `${name}.sol`, `${name}.json`);
    return JSON.parse(fs.readFileSync(p, "utf8"));
  };

  const idArtifact = readArtifact("StudentIdentity");
  const idFactory = new quais.ContractFactory(idArtifact.abi, idArtifact.bytecode, wallet);
  const identity = await idFactory.deploy();
  await identity.waitForDeployment();
  const identityAddress = await identity.getAddress();
  console.log("StudentIdentity:", identityAddress);

  const escrowArtifact = readArtifact("MarketplaceEscrow");
  const escrowFactory = new quais.ContractFactory(
    escrowArtifact.abi,
    escrowArtifact.bytecode,
    wallet
  );
  const escrow = await escrowFactory.deploy(identityAddress);
  await escrow.waitForDeployment();
  const escrowAddress = await escrow.getAddress();
  console.log("MarketplaceEscrow:", escrowAddress);

  const meta = {
    network: TARGET,
    chainId: CHAIN_ID,
    zone: "cyprus-1",
    rpc: RPC_URL,
    identity: identityAddress,
    escrow: escrowAddress,
    deployedAt: new Date().toISOString(),
  };
  const outDir = path.join(__dirname, "..", "abi");
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, `${TARGET}-deployment.json`);
  fs.writeFileSync(outFile, JSON.stringify(meta, null, 2));
  console.log(`Wrote abi/${TARGET}-deployment.json`);

  // Also copy ABIs into the backend so QUAI_CONTRACT_ADDRESS /
  // QUAI_ESCROW_CONTRACT_ADDRESS have matching interfaces on hand.
  const backendAbiDir = path.join(__dirname, "..", "..", "backend", "app", "contracts");
  if (fs.existsSync(backendAbiDir)) {
    fs.writeFileSync(
      path.join(backendAbiDir, "student_identity_abi.json"),
      JSON.stringify(idArtifact.abi, null, 2)
    );
    fs.writeFileSync(
      path.join(backendAbiDir, "marketplace_escrow_abi.json"),
      JSON.stringify(escrowArtifact.abi, null, 2)
    );
    console.log("ABIs copied to backend/app/contracts/");
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});