import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import { Navbar } from "../components/common/Navbar";

export const metadata: Metadata = {
  title: "CampusOS — Trusted African University Operating System",
  description: "The Trusted Digital Operating System for African Universities.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <Providers>
          <Navbar />

          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          <footer className="bg-white border-t border-slate-200 py-6 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
              <p>© 2026 CampusOS.</p>
              <div className="flex items-center gap-4">
                <span>Powered by Quai Network & Blip Pay</span>
                <span>●</span>
                <span>Off-Chain PII + On-Chain SHA-256 Hash Proofs</span>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
