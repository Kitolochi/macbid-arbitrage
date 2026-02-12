import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "MacBid Arbitrage",
  description: "Find profitable resale opportunities from MacBid auctions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-64 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
