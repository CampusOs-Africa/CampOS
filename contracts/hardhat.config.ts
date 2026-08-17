import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

dotenv.config();

// Official Quai Orchard Testnet (Cyprus-1 zone).
const ORCHARD_RPC =
  process.env.QUAI_RPC_URL || "https://orchard.rpc.quai.network/cyprus1";
const ORCHARD_CHAIN_ID = Number(process.env.QUAI_CHAIN_ID || 15000);
// Server-side deployer key. Never commit a real key. The default zero key is for
// local Hardhat tests only and is funded via the test accounts.
const DEPLOYER_PRIVATE_KEY =
  process.env.QUAI_PRIVATE_KEY ||
  "0x0000000000000000000000000000000000000000000000000000000000000001";

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    hardhat: { chainId: 31337 },
    orchard: {
      url: ORCHARD_RPC,
      accounts: [DEPLOYER_PRIVATE_KEY],
      chainId: ORCHARD_CHAIN_ID,
    },
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};

export default config;
