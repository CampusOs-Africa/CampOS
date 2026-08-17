"use client";

import React, { useState } from "react";
import { Award, ShieldCheck, Search, Filter } from "lucide-react";
import Link from "next/link";

export interface TrustLeaderboardItem {
  user_id: string;
  name: string;
  email: string;
  school?: string | null;
  department?: string | null;
  trust_score: number;
  trust_badge: string;
  is_verified: boolean;
  rank: number;
}

interface TrustLeaderboardProps {
  entries: TrustLeaderboardItem[];
  onFilterChange?: (school: string, department: string) => void;
}

export const TrustLeaderboard: React.FC<TrustLeaderboardProps> = React.memo(
  ({ entries, onFilterChange }) => {
    const [selectedSchool, setSelectedSchool] = useState("all");
    const [selectedDept, setSelectedDept] = useState("all");

    const handleSchoolChange = (val: string) => {
      setSelectedSchool(val);
      if (onFilterChange) onFilterChange(val, selectedDept);
    };

    const handleDeptChange = (val: string) => {
      setSelectedDept(val);
      if (onFilterChange) onFilterChange(selectedSchool, val);
    };

    const getBadgeClass = (badge: string) => {
      switch (badge.toLowerCase()) {
        case "platinum":
          return "bg-slate-200 text-slate-900 border-slate-300";
        case "gold":
          return "bg-amber-100 text-amber-900 border-amber-300";
        case "silver":
          return "bg-slate-100 text-slate-800 border-slate-300";
        case "bronze":
          return "bg-amber-50 text-amber-800 border-amber-200";
        default:
          return "bg-red-50 text-red-800 border-red-200";
      }
    };

    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4">
        {/* Top Filters */}
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Award className="h-5 w-5 text-amber-500" />
            <h3 className="text-base font-extrabold text-slate-900">
              Campus Reputation Leaderboard
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedSchool}
              onChange={(e) => handleSchoolChange(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Schools</option>
              <option value="University of Lagos">University of Lagos</option>
              <option value="University of Jos">University of Jos</option>
              <option value="Ahmadu Bello University">Ahmadu Bello University</option>
              <option value="University of Ibadan">University of Ibadan</option>
            </select>

            <select
              value={selectedDept}
              onChange={(e) => handleDeptChange(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Economics">Economics</option>
              <option value="Law">Law</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 text-xs uppercase tracking-wider bg-slate-50/70">
                <th className="py-3 px-5 font-bold">Rank</th>
                <th className="py-3 px-5 font-bold">Student</th>
                <th className="py-3 px-5 font-bold">Institution</th>
                <th className="py-3 px-5 font-bold">Tier Badge</th>
                <th className="py-3 px-5 font-bold text-right">Trust Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {entries.map((item) => (
                <tr
                  key={item.user_id}
                  className="hover:bg-slate-50/80 transition-colors"
                >
                  <td className="py-4 px-5 font-extrabold text-slate-900">
                    #{item.rank}
                  </td>
                  <td className="py-4 px-5">
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/trust/${item.user_id}`}
                        className="font-bold text-slate-900 hover:text-primary-600 transition-colors"
                      >
                        {item.name}
                      </Link>
                      {item.is_verified && (
                        <span title="Verified Student Identity">
                          <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">{item.email}</div>
                  </td>
                  <td className="py-4 px-5 text-slate-600">
                    <div className="font-semibold text-slate-800">
                      {item.school || "Campus University"}
                    </div>
                    <div className="text-xs text-slate-500">
                      {item.department || "General Studies"}
                    </div>
                  </td>
                  <td className="py-4 px-5">
                    <span
                      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold border ${getBadgeClass(
                        item.trust_badge
                      )}`}
                    >
                      ● {item.trust_badge}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-right font-black text-slate-900 text-base">
                    {item.trust_score}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
);

TrustLeaderboard.displayName = "TrustLeaderboard";
