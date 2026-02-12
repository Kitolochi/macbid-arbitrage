"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/opportunities", label: "Opportunities", icon: "💰" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
      <div className="px-6 py-6">
        <h1 className="text-xl font-bold tracking-tight">MacBid Arbitrage</h1>
        <p className="text-xs text-gray-500 mt-1">Profit finder</p>
      </div>
      <nav className="px-3 space-y-1">
        {links.map((link) => {
          const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <span>{link.icon}</span>
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
