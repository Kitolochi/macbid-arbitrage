import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function roiColor(roi: number): string {
  if (roi >= 30) return "text-profit-high";
  if (roi >= 15) return "text-profit-mid";
  return "text-profit-low";
}

export function roiBgColor(roi: number): string {
  if (roi >= 30) return "bg-green-50 border-green-200";
  if (roi >= 15) return "bg-yellow-50 border-yellow-200";
  return "bg-red-50 border-red-200";
}

export function timeRemaining(closesAt: string | null): string {
  if (!closesAt) return "N/A";
  const diff = new Date(closesAt).getTime() - Date.now();
  if (diff <= 0) return "Ended";
  const hours = Math.floor(diff / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}
