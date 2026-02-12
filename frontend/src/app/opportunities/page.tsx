"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { api, type Opportunity } from "@/lib/api";
import { formatCurrency, formatPercent, roiColor, roiBgColor } from "@/lib/utils";

export default function OpportunitiesPage() {
  const [data, setData] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [sorting, setSorting] = useState<SortingState>([{ id: "profit", desc: true }]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState<string>("");

  useEffect(() => {
    api
      .getOpportunities({ limit: 200 })
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!platformFilter) return data;
    return data.filter((o) => o.sell_platform === platformFilter);
  }, [data, platformFilter]);

  const columns = useMemo<ColumnDef<Opportunity>[]>(
    () => [
      {
        accessorKey: "sell_platform",
        header: "Platform",
        cell: ({ getValue }) => (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium capitalize">
            {getValue<string>()}
          </span>
        ),
        size: 100,
      },
      {
        accessorKey: "buy_cost",
        header: "Buy Cost",
        cell: ({ getValue }) => formatCurrency(getValue<number>()),
      },
      {
        accessorKey: "estimated_sell_price",
        header: "Sell Price",
        cell: ({ getValue }) => formatCurrency(getValue<number>()),
      },
      {
        accessorKey: "platform_fees",
        header: "Fees",
        cell: ({ getValue }) => formatCurrency(getValue<number>()),
      },
      {
        accessorKey: "profit",
        header: "Profit",
        cell: ({ row }) => (
          <span className={`font-semibold ${roiColor(row.original.roi_pct)}`}>
            {formatCurrency(row.original.profit)}
          </span>
        ),
      },
      {
        accessorKey: "roi_pct",
        header: "ROI %",
        cell: ({ row }) => (
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ${roiBgColor(
              row.original.roi_pct
            )} ${roiColor(row.original.roi_pct)}`}
          >
            {formatPercent(row.original.roi_pct)}
          </span>
        ),
      },
      {
        accessorKey: "confidence_score",
        header: "Confidence",
        cell: ({ getValue }) => {
          const score = getValue<number>();
          return (
            <div className="flex items-center gap-2">
              <div className="h-2 w-16 rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-blue-500"
                  style={{ width: `${score}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">{score.toFixed(0)}</span>
            </div>
          );
        },
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <Link
            href={`/opportunities/${row.original.id}`}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Details →
          </Link>
        ),
        size: 80,
      },
    ],
    []
  );

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-500">Loading opportunities...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Opportunities</h2>
        <p className="text-gray-500 text-sm mt-1">{data.length} arbitrage opportunities found</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
        />
        <select
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="">All Platforms</option>
          <option value="ebay">eBay</option>
          <option value="amazon">Amazon</option>
          <option value="facebook">Facebook</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b border-gray-100">
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700"
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{ asc: " ↑", desc: " ↓" }[header.column.getIsSorted() as string] ?? ""}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-5 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
              {table.getRowModel().rows.length === 0 && (
                <tr>
                  <td colSpan={columns.length} className="px-5 py-12 text-center text-gray-400">
                    No opportunities found matching your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-gray-100 px-5 py-3">
          <p className="text-sm text-gray-500">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}–
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              filtered.length
            )}{" "}
            of {filtered.length}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium disabled:opacity-50 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
