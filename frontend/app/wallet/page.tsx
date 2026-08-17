"use client";
import { API_BASE_URL } from "../../lib/api";

import React, { useState, useEffect, useCallback } from "react";
import { BalanceCard } from "../../components/wallet/BalanceCard";
import { TransactionList, TransactionItem } from "../../components/wallet/TransactionList";
import { QRReceiveModal } from "../../components/wallet/QRReceiveModal";
import { SendModal } from "../../components/wallet/SendModal";
import { DepositModal } from "../../components/wallet/DepositModal";
import { WithdrawModal } from "../../components/wallet/WithdrawModal";
import { WalletSettings } from "../../components/wallet/WalletSettings";
import { Wallet, User, Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function WalletPage() {
  const { user } = useAuth();
  const [userId, setUserId] = useState(user?.id || "student-wallet-01");

  useEffect(() => {
    if (user?.id) {
      setUserId(user.id);
    }
  }, [user?.id]);
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [sendOpen, setSendOpen] = useState(false);
  const [receiveOpen, setReceiveOpen] = useState(false);
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Create user if not exists so demo always works
      await fetch(`${API_BASE_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Amina Bello",
          email: "amina@unijos.edu.ng",
          role: "student",
        }),
      }).catch(() => {});

      // Connect wallet if not connected
      await fetch(`${API_BASE_URL}/wallet/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          wallet_address: "0x1111111111111111111111111111111111111111",
          message: "CampusOS Web3 Auth Challenge",
          signature: "0xmock_signature_hex_65_bytes",
        }),
      }).catch(() => {});

      const res = await fetch(`${API_BASE_URL}/wallet/dashboard/${userId}`);
      if (!res.ok) {
        throw new Error("Failed to fetch Campus Wallet dashboard.");
      }
      const data = await res.json();
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message || "Error loading Campus Wallet.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Top Banner & Account Switcher */}
      <div className="border-b border-slate-200 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Wallet className="h-6 w-6 text-primary-600" />
            Quai Campus Wallet
          </h1>
          <p className="text-sm text-slate-500">
            Send, receive, and manage QUAI testnet tokens. Integrated with Verified Student Identity.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
          <User className="h-4 w-4 text-slate-500" />
          <span className="text-xs text-slate-500">Demo User ID:</span>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="bg-white border border-slate-300 rounded px-2 py-0.5 text-xs font-mono text-slate-800 w-36 focus:outline-none focus:border-primary-500"
          />
          <button
            onClick={fetchDashboard}
            className="p-1 rounded bg-white border border-slate-300 hover:bg-slate-50 text-slate-600"
            title="Reload Wallet"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {loading && !dashboardData ? (
        <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600 mb-3" />
          <p className="text-sm font-semibold">Connecting to Quai Network & loading Campus Wallet...</p>
        </div>
      ) : dashboardData ? (
        <>
          {/* Balance Card */}
          <BalanceCard
            userId={dashboardData.user_id}
            walletAddress={dashboardData.wallet_address}
            balanceQuai={dashboardData.balance?.balance_quai || 0}
            balanceWei={dashboardData.balance?.balance_wei}
            fiatValueNgn={dashboardData.balance?.fiat_value_ngn || 0}
            network={dashboardData.balance?.network}
            isVerified={dashboardData.is_verified}
            onSendClick={() => setSendOpen(true)}
            onReceiveClick={() => setReceiveOpen(true)}
            onDepositClick={() => setDepositOpen(true)}
            onWithdrawClick={() => setWithdrawOpen(true)}
            onSettingsClick={() => setSettingsOpen(true)}
            onRefresh={fetchDashboard}
          />

          {/* Transaction List */}
          <TransactionList
            transactions={dashboardData.transactions || []}
            loading={loading}
          />

          {/* Modals */}
          <SendModal
            isOpen={sendOpen}
            onClose={() => setSendOpen(false)}
            senderId={dashboardData.user_id}
            balanceQuai={dashboardData.balance?.balance_quai || 0}
            onSuccess={() => {
              setSendOpen(false);
              fetchDashboard();
            }}
          />

          <QRReceiveModal
            isOpen={receiveOpen}
            onClose={() => setReceiveOpen(false)}
            walletAddress={dashboardData.wallet_address || "0x1111111111111111111111111111111111111111"}
            userName="Amina Bello"
            isVerified={dashboardData.is_verified}
          />

          <DepositModal
            isOpen={depositOpen}
            onClose={() => setDepositOpen(false)}
            walletAddress={dashboardData.wallet_address || "0x1111111111111111111111111111111111111111"}
            userId={dashboardData.user_id}
            onSuccess={() => {
              setDepositOpen(false);
              fetchDashboard();
            }}
          />

          <WithdrawModal
            isOpen={withdrawOpen}
            onClose={() => setWithdrawOpen(false)}
            senderId={dashboardData.user_id}
            balanceQuai={dashboardData.balance?.balance_quai || 0}
            onSuccess={() => {
              setWithdrawOpen(false);
              fetchDashboard();
            }}
          />

          <WalletSettings
            isOpen={settingsOpen}
            onClose={() => setSettingsOpen(false)}
            userId={dashboardData.user_id}
            walletAddress={dashboardData.wallet_address || "0x1111111111111111111111111111111111111111"}
            onWalletConnected={() => {
              setSettingsOpen(false);
              fetchDashboard();
            }}
          />
        </>
      ) : (
        <div className="p-12 text-center text-red-600 bg-red-50 rounded-2xl border border-red-200">
          <p className="text-sm font-semibold">{error || "Failed to load Campus Wallet."}</p>
        </div>
      )}
    </div>
  );
}
