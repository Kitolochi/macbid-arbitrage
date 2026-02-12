const API_BASE = "/api";

export interface Product {
  id: string;
  upc: string | null;
  asin: string | null;
  title: string;
  category: string | null;
  image_url: string | null;
  created_at: string;
}

export interface Listing {
  id: string;
  listing_id: string;
  product_id: string;
  current_bid: number;
  retail_price: number | null;
  condition: string;
  warehouse_location: string | null;
  closes_at: string | null;
  status: string;
  url: string | null;
  created_at: string;
}

export interface PlatformPrice {
  id: string;
  platform: string;
  price: number;
  condition: string | null;
  shipping_cost: number;
  url: string | null;
  seller_info: string | null;
  fetched_at: string;
}

export interface Opportunity {
  id: string;
  product_id: string;
  macbid_listing_id: string;
  buy_cost: number;
  estimated_sell_price: number;
  sell_platform: string;
  platform_fees: number;
  shipping_cost: number;
  profit: number;
  roi_pct: number;
  confidence_score: number;
  created_at: string;
}

export interface OpportunityDetail extends Opportunity {
  product: Product;
  listing: Listing;
  platform_prices: PlatformPrice[];
}

export interface DashboardStats {
  total_opportunities: number;
  avg_profit: number;
  avg_roi: number;
  top_categories: { category: string; count: number }[];
  active_listings: number;
  recent_opportunities: Opportunity[];
}

export interface AlertSetting {
  id: string;
  email: string;
  min_profit: number;
  min_roi: number;
  watched_categories: string[] | null;
  is_active: boolean;
  created_at: string;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getOpportunities(params?: {
    sort_by?: string;
    sort_dir?: string;
    platform?: string;
    min_profit?: number;
    min_roi?: number;
    limit?: number;
    offset?: number;
  }) {
    const search = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) search.set(k, String(v));
      });
    }
    const qs = search.toString();
    return fetchJson<Opportunity[]>(`/opportunities${qs ? `?${qs}` : ""}`);
  },

  getOpportunity(id: string) {
    return fetchJson<OpportunityDetail>(`/opportunities/${id}`);
  },

  getListings(params?: { status?: string; limit?: number; offset?: number }) {
    const search = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) search.set(k, String(v));
      });
    }
    const qs = search.toString();
    return fetchJson<Listing[]>(`/listings${qs ? `?${qs}` : ""}`);
  },

  getProductPrices(productId: string) {
    return fetchJson<PlatformPrice[]>(`/products/${productId}/prices`);
  },

  getDashboardStats() {
    return fetchJson<DashboardStats>("/dashboard/stats");
  },

  getAlertSettings() {
    return fetchJson<AlertSetting[]>("/alerts/settings");
  },

  createAlertSetting(data: Omit<AlertSetting, "id" | "created_at">) {
    return fetchJson<AlertSetting>("/alerts/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  updateAlertSetting(id: string, data: Omit<AlertSetting, "id" | "created_at">) {
    return fetchJson<AlertSetting>(`/alerts/settings/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
};
