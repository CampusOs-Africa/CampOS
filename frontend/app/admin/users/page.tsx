"use client";

import React, { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { adminFetch, ApiError } from "../../../lib/adminApi";

type AdminUser = {
  id: string;
  name: string;
  email: string;
  role: string;
  verification_status: string;
  is_active: boolean;
  trust_score: number;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    adminFetch<AdminUser[]>("/admin/users")
      .then(setUsers)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed"))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const changeRole = async (id: string, role: string) => {
    if (!window.confirm(`Change role to '${role}'?`)) return;
    await adminFetch(`/admin/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    load();
  };

  const toggleActive = async (u: AdminUser) => {
    await adminFetch(`/admin/users/${u.id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !u.is_active }),
    });
    load();
  };

  if (loading) return <Loader2 className="h-5 w-5 animate-spin text-slate-400" />;
  if (error)
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex gap-2">
        <AlertCircle className="h-5 w-5" /> {error}
      </div>
    );

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="p-3">Name</th>
            <th className="p-3">Email</th>
            <th className="p-3">Role</th>
            <th className="p-3">Verification</th>
            <th className="p-3">Trust</th>
            <th className="p-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {users.map((u) => (
            <tr key={u.id}>
              <td className="p-3 font-medium text-slate-800">{u.name}</td>
              <td className="p-3 text-slate-600">{u.email}</td>
              <td className="p-3">
                <select
                  defaultValue={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value)}
                  className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
                >
                  <option value="student">student</option>
                  <option value="verified_student">verified_student</option>
                  <option value="moderator">moderator</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td className="p-3">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold">{u.verification_status}</span>
              </td>
              <td className="p-3">{u.trust_score}</td>
              <td className="p-3 text-right">
                <button
                  onClick={() => toggleActive(u)}
                  className={`rounded-lg px-2 py-1 text-xs font-bold ${
                    u.is_active ? "border border-red-300 text-red-700 hover:bg-red-50" : "bg-emerald-600 text-white hover:bg-emerald-500"
                  }`}
                >
                  {u.is_active ? "Deactivate" : "Activate"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
