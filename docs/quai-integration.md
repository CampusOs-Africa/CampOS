# CampusOS Quai Integration

**Status:** Orchard Testnet integration code COMPLETE; live on-chain deployment
is BLOCKED pending a funded Cyprus-1 deployer key. Contracts compile and all
24 contract tests pass locally.

## Network

- **Target:** Quai Orchard Testnet, Cyprus-1 zone
- Chain ID: `15000` (`0x3A98`)
- RPC: `https://orchard.rpc.quai.network/cyprus1`
- GraphQL: `https://orchard.graph.quai.network`
- Explorer: `https://orchard.quaiscan.io`
- Faucet: `https://orchard.faucet.quai.network`

Production (mainnet) uses chain ID `9` at `https://rpc.quai.network/cyprus1`.
Set `QUAI_NETWORK` / `QUAI_CHAIN_ID` / `QUAI_RPC_URL` accordingly.

## Contracts

Two Solidity 0.8.20 contracts:

1. **CampusIdentityRegistry** (formerly `StudentIdentity.sol`)
   - Owner/admin registers a student's SHA-256 credential commitment.
   - `verifyStudent`, `revokeStudent`, `isVerified`, `getCredentialHash`.
   - No PII is stored on-chain (only a bytes32 hash and boolean).
   - Events: `StudentVerified`, `StudentRevoked`.
2. **CampusEscrow** (formerly `MarketplaceEscrow.sol`)
   - Lifecycle: `CREATED → FUNDED → DELIVERED → COMPLETED`; with
     `REFUNDED`, `CANCELLED`, `DISPUTED`.
   - Buyer deposits native QUAI; release/refund are role-gated and protected
     by OpenZeppelin `ReentrancyGuard`.
   - Only verified students (via the identity registry) can be sellers.
   - Events for every state transition.

ABIs are emitted to `contracts/abi/` on compile and deployed via the Quais SDK
script `scripts/deployQuai.ts`.

## Blip wallet (frontend)

`frontend/lib/blip.ts` wraps the injected EIP-1193 provider:

- Detects `window.quai` (preferred), `window.pelagus`, or the Blip-marked
  `window.ethereum`.
- Connects with `quai_requestAccounts`; verifies chain and switches to Orchard
  (`wallet_switchEthereumChain` / `wallet_addEthereumChain`).
- Sends `quai_sendTransaction` for the escrow deposit and returns a tx hash.
- Supports `blip_requestAppWalletFunding` for native gas top-ups.

**CampusOS never receives or stores a private key.** Signing happens in the
Blip app on the user's device.

## Transaction lifecycle

```
Buyer → POST /payments/intent            (server creates PaymentIntent)
      → Blip: quai_sendTransaction       (buyer approves deposit)
      → POST /payments/intent/{id}/confirm  (submits tx hash)
      → backend QuaiVerificationService.verify_escrow_funding()
          - quai_getTransactionReceipt
          - confirms tx success
          - confirms target == CampusEscrow
          - finds EscrowFunded log with the orderId topic
      → PaymentIntent marked paid
      → OrderService locks order/escrow
```

The frontend tx hash is a **UX reference only**. The backend independently
queries Orchard and verifies the receipt, contract address, and event before
marking anything paid.

## Order ID commitment

The on-chain `orderId` is `sha256(CampusOS order UUID)` as bytes32. The backend
returns `order_id_hex` on the PaymentIntent so the frontend can ABI-encode
`deposit(bytes32)` without a keccak library.

## Money representation

`PaymentIntent.amount_minor` is stored as a **decimal string of wei** (QUAI has
18 decimals). SQLite integers are 64-bit and cannot hold >~9 QUAI; using a
string keeps 256-bit EVM values portable across SQLite and Postgres. The
contract and on-chain amounts are in wei.

> **NGN → QUAI conversion is NOT implemented.** Blip is a self-custody wallet,
> not an NGN fiat ramp. A future verified ramp/quote provider must supply the
> authoritative conversion; the frontend must never calculate it.

## Configuration

Backend:
```
QUAI_NETWORK=orchard
QUAI_CHAIN_ID=15000
QUAI_RPC_URL=https://orchard.rpc.quai.network/cyprus1
CAMPUS_IDENTITY_CONTRACT_ADDRESS=
CAMPUS_ESCROW_CONTRACT_ADDRESS=
```
Frontend:
```
NEXT_PUBLIC_QUAI_RPC_URL=https://orchard.rpc.quai.network/cyprus1
NEXT_PUBLIC_QUAI_CHAIN_ID=15000
NEXT_PUBLIC_CAMPUS_ESCROW_ADDRESS=
NEXT_PUBLIC_CAMPUS_IDENTITY_ADDRESS=
```

## Deployment (pending funded key)

```
cd contracts
QUAI_PRIVATE_KEY=<cyprus-1 funded key> \
  npx hardhat run scripts/deployQuai.ts
```

This writes `abi/orchard-deployment.json`. Copy the addresses into the
backend/frontend environment. The deployer key must correspond to a Cyprus-1
zone address (Quai uses zone-aware derivation via the Quais SDK).

## Privacy model

On-chain: 32-byte credential commitment, verification boolean, escrow
order/amount/buyer/seller. No names, emails, phone numbers, matric numbers,
or document URLs.

## Remaining blocker

A funded Orchard Cyprus-1 deployer private key (zone-correct) is required to
broadcast the deploy and end-to-end on-chain transaction. Without it,
contracts are compiled/tested but not deployed.
