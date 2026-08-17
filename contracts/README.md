# CampusOS — Smart Contracts (Milestone 3: Verified Student Identity on Quai Network)

This repository contains the official **Quai Network** smart contracts for **CampusOS**, the trusted digital operating system for African universities built for the **Quai × Blip Buildathon**.

---

## 1. Smart Contract Overview

### `StudentIdentity.sol`
* **Purpose:** Stores immutable cryptographic proofs of verified university student identities.
* **Privacy By Design:** Stores **ONLY SHA-256 cryptographic credential hashes (`bytes32`) and verification boolean flags (`isVerified`)**. No Personally Identifiable Information (PII) such as student names, ID numbers, admission letters, or email addresses is ever stored on-chain.
* **Access Control:** All administrative registration, verification, and revocation actions are protected by the `onlyOwner` modifier (contract administrator / CampusOS backend service wallet).

### Public Contract Methods
| Function Signature | Modifier | Description |
| :--- | :--- | :--- |
| `registerStudent(address user, bytes32 credHash)` | `onlyOwner` | Registers a student's SHA-256 credential hash (`bytes32`), marks `isVerified = true`, and emits `StudentRegistered`. |
| `verifyStudent(address user)` | `onlyOwner` | Re-verifies a registered student account and emits `StudentVerified`. |
| `revokeStudent(address user)` | `onlyOwner` | Sets `isVerified = false` and emits `StudentRevoked` while preserving the SHA-256 hash for auditability. |
| `isVerified(address user) external view returns (bool)` | `external view` | Public query returning whether `user` is currently verified on Quai Network. |
| `getCredentialHash(address user) external view returns (bytes32)` | `external view` | Public query returning the SHA-256 cryptographic credential hash stored on Quai Network. |

---

## 2. Environment Setup (.env)

Create a `.env` file in `/home/user/contracts/` (or copy from root `.env`):
```env
QUAI_RPC_URL=https://rpc.quai.network
QUAI_PRIVATE_KEY=0xYourDeployerPrivateKeyHere
```

---

## 3. Running Automated Test Suites

### Hardhat + Chai Test Suite (EVM Local Node)
```bash
cd /home/user/contracts
npm test
# Or: npx hardhat test
```
**Test Coverage (`test/StudentIdentity.test.ts`):**
* Verifies `registerStudent()`, `verifyStudent()`, `revokeStudent()`, and public view getters.
* Verifies rejection of zero addresses and empty credential hashes.
* Verifies `onlyOwner` access control rejection for unauthorized callers.
* Verifies emission of `StudentRegistered`, `StudentVerified`, and `StudentRevoked` events.

### Foundry Test Suite
```bash
cd /home/user/contracts
forge test -vv
```

---

## 4. Deploying to Quai Network Testnet

To deploy `StudentIdentity.sol` to the Quai Network testnet:
```bash
cd /home/user/contracts
npm run deploy:quai-testnet
# Or: npx hardhat run scripts/deploy.ts --network quaiTestnet
```

### Automatic Deployment Artifacts
Upon successful deployment, the deployment script automatically:
1. Logs the deployed contract address and Quai transaction hash.
2. Saves deployment metadata to `abi/StudentIdentityDeployment.json`.
3. Exports the Solidity ABI to `abi/StudentIdentity.json` and automatically synchronizes it with `/home/user/backend/app/contracts/student_identity_abi.json` for backend integration.
