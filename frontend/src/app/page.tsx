"use client";

import { useEffect, useState } from "react";
import { api, type DashboardStats, type Opportunity } from "@/lib/api";
import { formatCurrency, formatPercent, roiColor } from "@/lib/utils";
import Link from "next/link";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [sseOpps, setSseOpps] = useState<Opportunity[]>([]);

  useEffect(() => {
    api.getDashboardStats().then(setStats).finally(() => setLoading(false));

    // SSE for real-time updates
    const es = new EventSource("/api/stream");
    es.addEventListener("new_opportunity", (e) => {
      const data = JSON.parse(e.data);
      setSseOpps((prev) => [data, ...prev].slice(0, 5));
    });
    return () => es.close();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-500">Loading dashboard...</div>;
  }

  if (!stats) {
    return <div className="text-gray-500">Failed to load dashboard data. Is the backend running?</div>;
  }

  const cards = [
    { label: "Active Opportunities", value: stats.total_opportunities, fmt: String },
    { label: "Avg Profit", value: stats.avg_profit, fmt: formatCurrency },
    { label: "Avg ROI", value: stats.avg_roi, fmt: formatPercent },
    { label: "Active Listings", value: stats.active_listings, fmt: String },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="text-gray-500 text-sm mt-1">Overview of arbitrage opportunities</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{card.label}</p>
            <p className="mt-2 text-2xl font-semibold">{card.fmt(card.value)}</p>
          </div>
        ))}
      </div>

      {/* Real-time SSE feed */}
      {sseOpps.length > 0 && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">Live Updates</h3>
          <div className="space-y-1">
            {sseOpps.map((opp, i) => (
              <div key={i} className="text-sm text-blue-700">
                New {opp.sell_platform} opportunity: {formatCurrency(opp.profit)} profit ({formatPercent(opp.roi_pct)} ROI)
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top categories */}
      {stats.top_categories.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Categories</h3>
          <div className="flex flex-wrap gap-2">
            {stats.top_categories.map((cat) => (
              <span key={cat.category} className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-sm">
                {cat.category}
                <span className="text-xs text-gray-500">({cat.count})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent opportunities table */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700">Recent Opportunities</h3>
            <Link href="/opportunities" className="text-sm text-blue-600 hover:text-blue-800">
              View all →
            </Link>
          </div>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
              <th className="px-5 py-3">Platform</th>
              <th className="px-5 py-3">Buy Cost</th>
              <th className="px-5 py-3">Sell Price</th>
              <th className="px-5 py-3">Profit</th>
              <th className="px-5 py-3">ROI</th>
              <th className="px-5 py-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_opportunities.map((opp) => (
              <tr key={opp.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-5 py-3 capitalize">{opp.sell_platform}</td>
                <td className="px-5 py-3">{formatCurrency(opp.buy_cost)}</td>
                <td className="px-5 py-3">{formatCurrency(opp.estimated_sell_price)}</td>
                <td className={`px-5 py-3 font-medium ${roiColor(opp.roi_pct)}`}>
                  {formatCurrency(opp.profit)}
                </td>
                <td className={`px-5 py-3 font-medium ${roiColor(opp.roi_pct)}`}>
                  {formatPercent(opp.roi_pct)}
                </td>
                <td className="px-5 py-3">{opp.confidence_score.toFixed(0)}/100</td>
              </tr>
            ))}
            {stats.recent_opportunities.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-gray-400">
                  No opportunities yet. Wait for the scraper to run.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
