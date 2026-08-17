"use client";

/**
 * Blip wallet/provider integration.
 *
 * Blip is a self-custody Quai wallet that injects an EIP-1193 provider
 * (window.quai / window.pelagus / window.ethereum). Keys never leave the
 * device; CampusOS only requests signatures/transactions after user approval.
 *
 * Official docs: https://blippay.me/docs
 */

export const ORCHARD_CHAIN_ID = 15000; // decimal; 0x3A98
export const ORCHARD_CHAIN_ID_HEX = "0x3A98";
export const ORCHARD_RPC_URL = "https://orchard.rpc.quai.network/cyprus1";
export const ORCHARD_EXPLORER = "https://orchard.quaiscan.io";

export type BlipProvider = {
  isBlip?: boolean;
  _isSwiftBlip?: boolean;
  isMetaMask?: boolean;
  request: (args: { method: string; params?: unknown[] | object }) => Promise<unknown>;
  on?: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, handler: (...args: unknown[]) => void) => void;
};

declare global {
  interface Window {
    quai?: BlipProvider;
    pelagus?: BlipProvider;
    ethereum?: BlipProvider;
  }
}

/** Detect the preferred injected Blip/Quai provider (window.quai preferred). */
export function detectBlip(): BlipProvider | null {
  if (typeof window === "undefined") return null;
  if (window.quai) return window.quai;
  if (window.pelagus) return window.pelagus;
  if (window.ethereum && (window.ethereum as BlipProvider).isBlip) {
    return window.ethereum;
  }
  return null;
}

export function isBlipProvider(p: BlipProvider | null | undefined): boolean {
  return Boolean(p && (p.isBlip || p._isSwiftBlip));
}

/** Request connected accounts using quai_requestAccounts. */
export async function connectBlip(provider?: BlipProvider): Promise<string> {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("Blip wallet not detected. Open this page inside the Blip in-app browser.");
  const accounts = (await p.request({ method: "quai_requestAccounts" })) as string[];
  if (!accounts || accounts.length === 0) throw new Error("No account returned by Blip.");
  return accounts[0];
}

export async function getAccounts(provider?: BlipProvider): Promise<string[]> {
  const p = provider ?? detectBlip();
  if (!p) return [];
  return (await p.request({ method: "quai_accounts" })) as string[];
}

export async function getChainId(provider?: BlipProvider): Promise<number> {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("No provider.");
  const hex = (await p.request({ method: "quai_chainId" })) as string;
  return parseInt(hex, 16);
}

export async function getProviderState(provider?: BlipProvider) {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("No provider.");
  return p.request({ method: "wallet_getProviderState" });
}

/** Ensure the wallet is on the Orchard testnet; prompt switch if not. */
export async function ensureOrchard(provider?: BlipProvider): Promise<void> {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("No provider.");
  const chainId = await getChainId(p);
  if (chainId === ORCHARD_CHAIN_ID) return;
  try {
    await p.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: ORCHARD_CHAIN_ID_HEX }],
    });
  } catch {
    await p.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId: ORCHARD_CHAIN_ID_HEX,
          chainName: "Quai Orchard Testnet (Cyprus-1)",
          nativeCurrency: { name: "QUAI", symbol: "QUAI", decimals: 18 },
          rpcUrls: [ORCHARD_RPC_URL],
          blockExplorerUrls: [ORCHARD_EXPLORER],
        },
      ],
    });
  }
}

export async function requestAppWalletFunding(
  amountWei: bigint,
  provider?: BlipProvider,
): Promise<unknown> {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("No provider.");
  return p.request({
    method: "blip_requestAppWalletFunding",
    params: [{ amount: "0x" + amountWei.toString(16) }],
  });
}

export type TxParams = {
  to: string;
  value: bigint | string;
  data?: string;
  gas?: bigint | string;
};

/** Submit a transaction via the Blip/Quai provider. Returns a tx hash. */
export async function sendTransaction(
  tx: TxParams,
  provider?: BlipProvider,
): Promise<string> {
  const p = provider ?? detectBlip();
  if (!p) throw new Error("No provider.");
  const normalize = (v: bigint | string) =>
    typeof v === "bigint" ? "0x" + v.toString(16) : v;
  const hash = (await p.request({
    method: "quai_sendTransaction",
    params: [
      {
        to: tx.to,
        value: normalize(tx.value),
        data: tx.data ?? "0x",
        ...(tx.gas ? { gas: normalize(tx.gas) } : {}),
      },
    ],
  })) as string;
  return hash;
}

export function listenForWalletEvents(
  handlers: { onAccountsChanged?: (a: string[]) => void; onChainChanged?: (c: number) => void },
  provider?: BlipProvider,
): () => void {
  const p = provider ?? detectBlip();
  if (!p || !p.on || !p.removeListener) return () => {};
  const ac = (a: unknown) => handlers.onAccountsChanged?.(a as string[]);
  const cc = (c: unknown) =>
    handlers.onChainChanged?.(parseInt(c as string, 16));
  p.on("accountsChanged", ac);
  p.on("chainChanged", cc);
  return () => {
    p.removeListener?.("accountsChanged", ac);
    p.removeListener?.("chainChanged", cc);
  };
}

/** Open a dApp URL inside the Blip in-app browser. */
export function openInBlip(url: string): void {
  if (typeof window !== "undefined") {
    window.location.href = `https://blippay.me/browser?url=${encodeURIComponent(url)}`;
  }
}
