import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

dotenv.config();

// --- Orchard Testnet (Cyprus-1 zone) ---
const TESTNET_RPC =
  process.env.QUAI_TESTNET_RPC_URL || "https://orchard.rpc.quai.network/cyprus1";
const TESTNET_CHAIN_ID = Number(process.env.QUAI_TESTNET_CHAIN_ID || 15000);
// A funded Cyprus-1 deployer key is required for testnet deployment.
const TESTNET_PRIVATE_KEY = process.env.QUAI_TESTNET_PRIVATE_KEY || "";

// --- Quai Mainnet (Cyprus-1 zone, chain ID 9) ---
const MAINNET_RPC =
  process.env.QUAI_MAINNET_RPC_URL || "https://rpc.quai.network/cyprus1";
const MAINNET_CHAIN_ID = Number(process.env.QUAI_MAINNET_CHAIN_ID || 9);
// Intentionally NO fallback key for mainnet — if QUAI_MAINNET_PRIVATE_KEY is
// unset, the mainnet network has zero configured accounts and any deploy
// attempt fails loudly instead of silently deploying with a throwaway key.
const MAINNET_PRIVATE_KEY = process.env.QUAI_MAINNET_PRIVATE_KEY || "";

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    hardhat: { chainId: 31337 },
    quaiTestnet: {
      url: TESTNET_RPC,
      accounts: TESTNET_PRIVATE_KEY ? [TESTNET_PRIVATE_KEY] : [],
      chainId: TESTNET_CHAIN_ID,
    },
    quaiMainnet: {
      url: MAINNET_RPC,
      accounts: MAINNET_PRIVATE_KEY ? [MAINNET_PRIVATE_KEY] : [],
      chainId: MAINNET_CHAIN_ID,
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