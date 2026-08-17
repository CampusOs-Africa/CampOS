#!/usr/bin/env bash
set -eo pipefail

echo "==> CampusOS Quai Network Smart Contract Deployment Entrypoint"
echo "==> Network: ${QUAI_NETWORK:-hardhat}"

echo "==> Compiling Solidity smart contracts..."
npx hardhat compile

if [ "${RUN_TESTS:-false}" = "true" ]; then
    echo "==> Executing Hardhat automated test suite..."
    npx hardhat test
fi

if [ "${DEPLOY_CONTRACTS:-true}" = "true" ]; then
    echo "==> Deploying StudentIdentity and MarketplaceEscrow to ${QUAI_NETWORK:-hardhat}..."
    npx hardhat run scripts/deployEscrow.ts --network "${QUAI_NETWORK:-hardhat}"
fi
