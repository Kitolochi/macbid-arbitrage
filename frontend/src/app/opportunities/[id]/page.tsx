"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { api, type OpportunityDetail } from "@/lib/api";
import { formatCurrency, formatPercent, roiColor, roiBgColor, timeRemaining } from "@/lib/utils";

export default function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [opp, setOpp] = useState<OpportunityDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getOpportunity(id).then(setOpp).finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-500">Loading...</div>;
  }

  if (!opp) {
    return <div className="text-gray-500">Opportunity not found.</div>;
  }

  const feeBreakdown = [
    { name: "Buy Cost", value: opp.buy_cost },
    { name: "Platform Fees", value: opp.platform_fees },
    { name: "Shipping", value: opp.shipping_cost },
    { name: "Profit", value: Math.max(opp.profit, 0) },
  ];

  const priceHistory = opp.platform_prices.map((p) => ({
    date: new Date(p.fetched_at).toLocaleDateString(),
    price: p.price,
    platform: p.platform,
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/opportunities" className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-block">
            ← Back to opportunities
          </Link>
          <h2 className="text-2xl font-bold">{opp.product.title}</h2>
          <div className="flex items-center gap-3 mt-2">
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium capitalize">
              {opp.sell_platform}
            </span>
            <span className="text-sm text-gray-500">
              Condition: <span className="capitalize">{opp.listing.condition.replace("_", " ")}</span>
            </span>
            {opp.listing.closes_at && (
              <span className="text-sm text-gray-500">
                Closes: {timeRemaining(opp.listing.closes_at)}
              </span>
            )}
          </div>
        </div>
        <div className={`rounded-xl border p-4 text-center ${roiBgColor(opp.roi_pct)}`}>
          <p className="text-xs font-medium text-gray-500 uppercase">ROI</p>
          <p className={`text-3xl font-bold ${roiColor(opp.roi_pct)}`}>{formatPercent(opp.roi_pct)}</p>
          <p className={`text-lg font-semibold ${roiColor(opp.roi_pct)}`}>{formatCurrency(opp.profit)} profit</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price comparison */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Price Comparison</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">MacBid Current Bid</span>
              <span className="font-medium">{formatCurrency(opp.listing.current_bid)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">+ Buyer Premium (15%)</span>
              <span className="font-medium">{formatCurrency(opp.listing.current_bid * 0.15)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">+ Lot Fee</span>
              <span className="font-medium">$3.00</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-200 font-semibold">
              <span>Total Buy Cost</span>
              <span>{formatCurrency(opp.buy_cost)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100 mt-4">
              <span className="text-gray-600">Est. Sell Price ({opp.sell_platform})</span>
              <span className="font-medium">{formatCurrency(opp.estimated_sell_price)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">− Platform Fees</span>
              <span className="font-medium text-red-600">-{formatCurrency(opp.platform_fees)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">− Shipping</span>
              <span className="font-medium text-red-600">-{formatCurrency(opp.shipping_cost)}</span>
            </div>
            <div className={`flex justify-between items-center py-2 font-bold text-lg ${roiColor(opp.roi_pct)}`}>
              <span>Net Profit</span>
              <span>{formatCurrency(opp.profit)}</span>
            </div>
          </div>
        </div>

        {/* Fee breakdown chart */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Cost Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={feeBreakdown} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={(v) => `$${v}`} />
              <YAxis type="category" dataKey="name" width={100} />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Price history chart */}
        {priceHistory.length > 1 && (
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm lg:col-span-2">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Price History</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={priceHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Comparable listings */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Comparable Listings ({opp.platform_prices.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  <th className="px-4 py-2">Platform</th>
                  <th className="px-4 py-2">Price</th>
                  <th className="px-4 py-2">Condition</th>
                  <th className="px-4 py-2">Shipping</th>
                  <th className="px-4 py-2">Fetched</th>
                  <th className="px-4 py-2">Link</th>
                </tr>
              </thead>
              <tbody>
                {opp.platform_prices.map((p) => (
                  <tr key={p.id} className="border-b border-gray-50">
                    <td className="px-4 py-2 capitalize">{p.platform}</td>
                    <td className="px-4 py-2 font-medium">{formatCurrency(p.price)}</td>
                    <td className="px-4 py-2">{p.condition || "—"}</td>
                    <td className="px-4 py-2">{formatCurrency(p.shipping_cost)}</td>
                    <td className="px-4 py-2 text-gray-500">{new Date(p.fetched_at).toLocaleString()}</td>
                    <td className="px-4 py-2">
                      {p.url && (
                        <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                          View →
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Action links */}
      <div className="flex gap-3">
        {opp.listing.url && (
          <a
            href={opp.listing.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            View on MacBid
          </a>
        )}
        {opp.product.upc && (
          <a
            href={`https://www.ebay.com/sch/i.html?_nkw=${opp.product.upc}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50"
          >
            Search eBay
          </a>
        )}
        {opp.product.asin && (
          <a
            href={`https://www.amazon.com/dp/${opp.product.asin}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50"
          >
            View on Amazon
          </a>
        )}
      </div>
    </div>
  );
}
