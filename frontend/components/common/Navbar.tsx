"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldAlert,
  Wallet,
  ShoppingBag,
  PackageCheck,
  User,
  LogOut,
  QrCode,
  LayoutDashboard,
  Menu,
  X,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { HeaderQRButton } from "./HeaderQRButton";

export function Navbar() {
  const { user, logout, loginWithDemoUser } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [demoMenuOpen, setDemoMenuOpen] = useState(false);

  const handleDemoSwitch = async (id: string) => {
    setDemoMenuOpen(false);
    const res = await loginWithDemoUser(id);
    if (res.success) router.push("/dashboard");
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold">
            C
          </div>
          <span className="font-bold text-lg tracking-tight text-slate-900">
            CampusOS
          </span>
          <span className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full font-semibold border border-primary-200 hidden lg:inline">
            African University OS
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-4 lg:gap-6 text-sm font-medium">
          <Link
            href="/"
            className={`transition-colors ${
              pathname === "/"
                ? "text-primary-600 font-bold"
                : "text-slate-700 hover:text-primary-600"
            }`}
          >
            Home
          </Link>

          <Link
            href="/marketplace"
            className={`inline-flex items-center gap-1 transition-colors ${
              pathname?.startsWith("/marketplace")
                ? "text-primary-600 font-bold"
                : "text-slate-700 hover:text-primary-600"
            }`}
          >
            <ShoppingBag className="h-4 w-4 text-primary-600" />
            <span>Marketplace</span>
          </Link>

          {!user ? (
            <>
              <Link
                href="/#about"
                className="text-slate-700 hover:text-primary-600 transition-colors"
              >
                About
              </Link>

              {/* Demo Account Quick Switcher */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setDemoMenuOpen(!demoMenuOpen)}
                  className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-colors"
                  title="Hackathon Demo: Quick Login"
                >
                  <Sparkles className="h-3 w-3 text-amber-600" />
                  <span>Demo Switcher</span>
                  <ChevronDown className="h-3 w-3" />
                </button>
                {demoMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-slate-200 py-1.5 z-50 text-xs">
                    <div className="px-3 py-1 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      1-Click Demo Accounts
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDemoSwitch("student-demo-001")}
                      className="w-full text-left px-3 py-2 hover:bg-slate-50 text-slate-700 font-medium flex items-center justify-between"
                    >
                      <span>Amina Bello (Student)</span>
                      <span className="text-emerald-600 font-bold">50 pt</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDemoSwitch("student-wallet-01")}
                      className="w-full text-left px-3 py-2 hover:bg-slate-50 text-slate-700 font-medium flex items-center justify-between"
                    >
                      <span>Chidi Okafor (Wallet)</span>
                      <span className="text-primary-600 font-bold">25 QUAI</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDemoSwitch("seller-01")}
                      className="w-full text-left px-3 py-2 hover:bg-slate-50 text-slate-700 font-medium flex items-center justify-between"
                    >
                      <span>Tunde Balogun (Seller)</span>
                      <span className="text-emerald-600 font-bold">Verified</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDemoSwitch("admin-001")}
                      className="w-full text-left px-3 py-2 hover:bg-slate-50 text-slate-700 font-medium flex items-center justify-between border-t border-slate-100 mt-1 pt-2"
                    >
                      <span>Dr. Nneka Eze (Admin)</span>
                      <span className="text-amber-600 font-bold">Admin</span>
                    </button>
                  </div>
                )}
              </div>

              <Link
                href="/login"
                className="text-slate-700 font-semibold hover:text-primary-600 transition-colors px-2 py-1"
              >
                Login
              </Link>

              <Link
                href="/signup"
                className="inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-primary-500 transition-all"
              >
                Sign Up
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/dashboard"
                className={`inline-flex items-center gap-1.5 transition-colors px-2.5 py-1.5 rounded-lg ${
                  pathname === "/dashboard"
                    ? "bg-primary-50 text-primary-700 font-bold border border-primary-200"
                    : "text-slate-700 hover:text-primary-600"
                }`}
              >
                <LayoutDashboard className="h-4 w-4 text-primary-600" />
                <span>Dashboard</span>
              </Link>

              <Link
                href="/orders"
                className={`inline-flex items-center gap-1 transition-colors ${
                  pathname?.startsWith("/orders")
                    ? "text-primary-600 font-bold"
                    : "text-slate-700 hover:text-primary-600"
                }`}
              >
                <PackageCheck className="h-4 w-4 text-emerald-600" />
                <span>Orders & Escrow</span>
              </Link>

              <Link
                href="/wallet"
                className={`inline-flex items-center gap-1 transition-colors ${
                  pathname?.startsWith("/wallet")
                    ? "text-primary-600 font-bold"
                    : "text-slate-700 hover:text-primary-600"
                }`}
              >
                <Wallet className="h-4 w-4 text-primary-600" />
                <span>Wallet</span>
              </Link>

              <Link
                href="/qr"
                className={`inline-flex items-center gap-1 transition-colors ${
                  pathname === "/qr" || pathname?.startsWith("/verification")
                    ? "text-primary-600 font-bold"
                    : "text-slate-700 hover:text-primary-600"
                }`}
              >
                <QrCode className="h-4 w-4 text-primary-600" />
                <span>QR ID</span>
              </Link>

              <HeaderQRButton />

              {user.role === "admin" && (
                <Link
                  href="/admin/verifications"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-all"
                >
                  <ShieldAlert className="h-3.5 w-3.5 text-primary-400" />
                  <span>Admin</span>
                </Link>
              )}

              <Link
                href="/profile"
                className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors ${
                  pathname === "/profile" ? "border-primary-400 bg-primary-50" : ""
                }`}
                title={`Logged in as ${user.name}`}
              >
                <User className="h-3.5 w-3.5 text-slate-600" />
                <span className="max-w-[100px] truncate">{user.name.split(" ")[0]}</span>
              </Link>

              <button
                type="button"
                onClick={() => { logout(); router.push("/"); }}
                className="inline-flex items-center gap-1 text-slate-500 hover:text-red-600 transition-colors text-xs font-medium"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </>
          )}
        </nav>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-2">
          <HeaderQRButton />
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-700 hover:bg-slate-100"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-2 shadow-lg">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            Home
          </Link>
          <Link
            href="/marketplace"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            Marketplace
          </Link>
          {!user ? (
            <>
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                Login
              </Link>
              <Link
                href="/signup"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium bg-primary-600 text-white text-center rounded-lg"
              >
                Sign Up
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                Dashboard
              </Link>
              <Link
                href="/orders"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                Orders & Escrow
              </Link>
              <Link
                href="/wallet"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                Wallet
              </Link>
              <Link
                href="/qr"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                QR ID Card
              </Link>
              <Link
                href="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                Profile ({user.name})
              </Link>
              <button
                type="button"
                onClick={() => {
                  logout();
                  setMobileMenuOpen(false);
                  router.push("/");
                }}
                className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-slate-50"
              >
                Logout
              </button>
            </>
          )}
        </div>
      )}
    </header>
  );
}
