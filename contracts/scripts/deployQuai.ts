/**
 * Quai-native deployment using the Quais SDK for Orchard Testnet (Cyprus-1).
 *
 * Usage:
 *   QUAI_PRIVATE_KEY=<hex> npx hardhat run scripts/deployQuai.ts
 *
 * The deployer key must be funded on Orchard Cyprus-1 and correspond to an
 * address in that zone. Unlike standard Hardhat/Ethers, Quai requires
 * zone-aware address derivation, which the Quais wallet handles.
 */
import { quais } from "quais";
import * as fs from "fs";
import * as path from "path";

const RPC_URL = process.env.QUAI_RPC_URL || "https://orchard.rpc.quai.network/cyprus1";
const CHAIN_ID = Number(process.env.QUAI_CHAIN_ID || 15000);

async function main() {
  const pk = process.env.QUAI_PRIVATE_KEY || process.env.QUAI_PRIVATE_KEY;
  if (!pk) throw new Error("QUAI_PRIVATE_KEY is required for Orchard deployment");

  const provider = new quais.JsonRpcProvider(RPC_URL);
  const wallet = new quais.Wallet(pk, provider);
  console.log("Deployer:", wallet.address);

  const balance = await provider.getBalance(wallet.address);
  console.log("Balance:", quais.formatQuai(balance), "QUAI");

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
  console.log("CampusIdentityRegistry:", identityAddress);

  const escrowArtifact = readArtifact("MarketplaceEscrow");
  const escrowFactory = new quais.ContractFactory(
    escrowArtifact.abi,
    escrowArtifact.bytecode,
    wallet
  );
  const escrow = await escrowFactory.deploy(identityAddress);
  await escrow.waitForDeployment();
  const escrowAddress = await escrow.getAddress();
  console.log("CampusEscrow:", escrowAddress);

  const meta = {
    network: "orchard",
    chainId: CHAIN_ID,
    zone: "cyprus-1",
    rpc: RPC_URL,
    identity: identityAddress,
    escrow: escrowAddress,
    deployedAt: new Date().toISOString(),
  };
  const outDir = path.join(__dirname, "..", "abi");
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "orchard-deployment.json"), JSON.stringify(meta, null, 2));
  console.log("Wrote abi/orchard-deployment.json");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
