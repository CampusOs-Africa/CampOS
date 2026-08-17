# Quai Orchard Deployment — Phase 9

## Status: BLOCKED AT DEPLOYMENT BOUNDARY

The Orchard Cyprus-1 RPC is **verified live** and all JSON-RPC methods required
by the backend verifier work. However, **no funded Cyprus-1 deployer private key
is available** in this environment, so the contracts have not been deployed.

Per the Phase 9 stop condition, no contract addresses or transaction hashes
are fabricated. Deployment is a one-command operation once a key is supplied.

## Orchard RPC verification (independently confirmed)

Endpoint: `https://orchard.rpc.quai.network/cyprus1`

| Check | Result |
|---|---|
| `eth_chainId` | `0x3a98` (= **15000**, Orchard) |
| `eth_blockNumber` | `0x73ce70` (and advancing) |
| Client version (extraData) | `quai-linux/v3.0.26.5` |
| `eth_getBalance` | works |
| `eth_getCode` | works (`0x` for EOA) |
| `eth_getTransactionReceipt` | works (`null` for unknown tx) |

The backend `QuaiVerificationService` uses exactly these read-only methods, so
it is ready to verify real transactions against the deployed escrow.

## Why deployment did not run

- `QUAI_PRIVATE_KEY` is not set in the environment or `contracts/.env`.
- The generic Hardhat default key maps to an address in a **different zone**;
  the Orchard Cyprus-1 node rejects it with
  `ProviderError: Address belongs to other zone`.
- Quai requires zone-aware key derivation (the Quais SDK). `scripts/deployQuai.ts`
  already uses Quais, but a funded Cyprus-1 key is still required.

## Exact next action

1. Obtain a Cyprus-1 Orchard account and fund it from the faucet:
   https://orchard.faucet.quai.network
2. Export its private key and provide it **only in the deploy environment**
   (never commit it):
   ```
   cd contracts
   echo "QUAI_PRIVATE_KEY=<hex>" > .env
   ```
3. Deploy:
   ```
   npx hardhat run scripts/deployQuai.ts --network orchard
   ```
   This writes `abi/orchard-deployment.json` with both addresses and the
   deployment tx hashes.
4. Configure CampusOS:
   ```
   # backend
   CAMPUS_IDENTITY_CONTRACT_ADDRESS=<address>
   CAMPUS_ESCROW_CONTRACT_ADDRESS=<address>
   QUAI_RPC_URL=https://orchard.rpc.quai.network/cyprus1
   QUAI_CHAIN_ID=15000
   QUAI_NETWORK=orchard
   # frontend
   NEXT_PUBLIC_CAMPUS_IDENTITY_CONTRACT_ADDRESS=<address>
   NEXT_PUBLIC_CAMPUS_ESCROW_CONTRACT_ADDRESS=<address>
   ```
5. Run one real purchase through the Blip in-app browser; the backend will
   independently verify the `EscrowFunded` event and mark the order paid.

## After deployment, the on-chain lifecycle is

`CREATED → FUNDED → DELIVERED → COMPLETED` (plus `REFUNDED`/`CANCELLED`/`DISPUTED`).

All 24 contract tests pass locally, validating state transitions, access
control, ReentrancyGuard, and the verified-seller gate.
