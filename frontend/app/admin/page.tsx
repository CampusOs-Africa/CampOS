"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, AlertCircle, Users, ShieldCheck, ShoppingBag, Package } from "lucide-react";
import { adminFetch, ApiError } from "../../lib/adminApi";

type Dashboard = {
  counts: Record<string, number>;
  escrow: { states: Record<string, number>; total_amount: number };
  payments: { total_order_amount: number };
  recent: {
    verifications: Array<{ id: string; user_id: string; status: string; university_email: string }>;
    fraud_reports: Array<{ id: string; reported_user_id: string; category: string; status: string }>;
    orders: Array<{ id: string; buyer_id: string; amount: number; status: string }>;
    listings: Array<{ id: string; title: string; status: string; price: number }>;
  };
};

function Card({ label, value, icon }: { label: string; value: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</span>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-extrabold text-slate-900">{value}</div>
    </div>
  );
}

function Badge({ status }: { status: string }) {
  const color =
    status === "approved" || status === "verified" || status === "completed"
      ? "bg-emerald-100 text-emerald-700"
      : status === "pending" || status === "initiated"
      ? "bg-amber-100 text-amber-700"
      : status === "rejected" || status === "revoked" || status === "suspended"
      ? "bg-red-100 text-red-700"
      : "bg-slate-100 text-slate-700";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${color}`}>{status}</span>
  );
}

export default function AdminDashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminFetch<Dashboard>("/admin/dashboard")
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex items-center text-slate-500">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading dashboard…
      </div>
    );
  if (error)
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 flex gap-2">
        <AlertCircle className="h-5 w-5" /> {error}
      </div>
    );
  if (!data) return null;

  const c = data.counts;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Users" value={c.users} icon={<Users className="h-4 w-4 text-slate-400" />} />
        <Card label="Verified" value={c.verified_students} icon={<ShieldCheck className="h-4 w-4 text-emerald-500" />} />
        <Card label="Pending Verif." value={c.pending_verifications} />
        <Card label="Pending Fraud" value={c.pending_fraud_reports} />
        <Card label="Active Listings" value={c.active_listings} icon={<ShoppingBag className="h-4 w-4 text-slate-400" />} />
        <Card label="Suspended" value={c.suspended_listings} />
        <Card label="Orders" value={c.orders} icon={<Package className="h-4 w-4 text-slate-400" />} />
        <Card label="Disputed" value={c.disputed_orders} />
        <Card label="Pending Orders" value={c.pending_orders} />
        <Card label="Completed Orders" value={c.completed_orders} />
        <Card label="Escrow Total" value={data.escrow.total_amount.toLocaleString()} />
        <Card label="Order Volume" value={data.payments.total_order_amount.toLocaleString()} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-slate-900">Verification queue</h2>
            <Link href="/admin/verifications" className="text-xs font-bold text-primary-600 hover:underline">View all</Link>
          </div>
          {data.recent.verifications.length === 0 ? <Empty text="No recent verifications" /> : (
            <ul className="divide-y divide-slate-100 text-sm">
              {data.recent.verifications.map((v) => (
                <li key={v.id} className="flex items-center justify-between py-2">
                  <div>
                    <div className="font-mono text-xs text-slate-500">{v.user_id}</div>
                    <div className="text-slate-700">{v.university_email}</div>
                  </div>
                  <Badge status={v.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-slate-900">Fraud reports</h2>
            <Link href="/admin/fraud" className="text-xs font-bold text-primary-600 hover:underline">View all</Link>
          </div>
          {data.recent.fraud_reports.length === 0 ? <Empty text="No recent fraud reports" /> : (
            <ul className="divide-y divide-slate-100 text-sm">
              {data.recent.fraud_reports.map((r) => (
                <li key={r.id} className="flex items-center justify-between py-2">
                  <span className="text-slate-700">{r.category}</span>
                  <Badge status={r.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="font-bold text-slate-900 mb-3">Recent orders</h2>
          {data.recent.orders.length === 0 ? <Empty text="No orders yet" /> : (
            <ul className="divide-y divide-slate-100 text-sm">
              {data.recent.orders.map((o) => (
                <li key={o.id} className="flex items-center justify-between py-2">
                  <span className="font-mono text-xs text-slate-500">{o.id.slice(0, 8)}</span>
                  <span className="text-slate-700">{o.amount}</span>
                  <Badge status={o.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="font-bold text-slate-900 mb-3">Recent listings</h2>
          {data.recent.listings.length === 0 ? <Empty text="No listings yet" /> : (
            <ul className="divide-y divide-slate-100 text-sm">
              {data.recent.listings.map((l) => (
                <li key={l.id} className="flex items-center justify-between py-2">
                  <span className="text-slate-700 truncate pr-2">{l.title}</span>
                  <Badge status={l.status} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-slate-400 py-6 text-center">{text}</p>;
}
