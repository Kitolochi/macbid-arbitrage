"use client";

import { useEffect, useState } from "react";
import { api, type AlertSetting } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AlertSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [email, setEmail] = useState("");
  const [minProfit, setMinProfit] = useState(10);
  const [minRoi, setMinRoi] = useState(20);
  const [categories, setCategories] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    try {
      const data = await api.getAlertSettings();
      setSettings(data);
    } finally {
      setLoading(false);
    }
  }

  function editSetting(s: AlertSetting) {
    setEditingId(s.id);
    setEmail(s.email);
    setMinProfit(s.min_profit);
    setMinRoi(s.min_roi);
    setCategories(s.watched_categories?.join(", ") || "");
  }

  function resetForm() {
    setEditingId(null);
    setEmail("");
    setMinProfit(10);
    setMinRoi(20);
    setCategories("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const payload = {
      email,
      min_profit: minProfit,
      min_roi: minRoi,
      watched_categories: categories ? categories.split(",").map((c) => c.trim()).filter(Boolean) : null,
      is_active: true,
    };

    try {
      if (editingId) {
        await api.updateAlertSetting(editingId, payload);
      } else {
        await api.createAlertSetting(payload);
      }
      resetForm();
      await loadSettings();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold">Settings</h2>
        <p className="text-gray-500 text-sm mt-1">Configure alert thresholds and notification preferences</p>
      </div>

      {/* Alert Settings Form */}
      <form onSubmit={handleSubmit} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm space-y-5">
        <h3 className="text-sm font-semibold text-gray-700">
          {editingId ? "Edit Alert" : "New Alert Setting"}
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Profit ($)</label>
            <input
              type="number"
              min={0}
              step={0.01}
              value={minProfit}
              onChange={(e) => setMinProfit(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Minimum ROI (%)</label>
            <input
              type="number"
              min={0}
              step={0.1}
              value={minRoi}
              onChange={(e) => setMinRoi(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Watched Categories</label>
          <input
            type="text"
            value={categories}
            onChange={(e) => setCategories(e.target.value)}
            placeholder="Electronics, Toys & Games, Home & Kitchen"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">Comma-separated. Leave blank to watch all categories.</p>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : editingId ? "Update Alert" : "Create Alert"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Existing Settings */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">Active Alerts</h3>
        </div>
        {loading ? (
          <div className="p-5 text-gray-400 text-sm">Loading...</div>
        ) : settings.length === 0 ? (
          <div className="p-5 text-gray-400 text-sm">No alert settings configured yet.</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {settings.map((s) => (
              <div key={s.id} className="px-5 py-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{s.email}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Min profit: ${s.min_profit} · Min ROI: {s.min_roi}%
                    {s.watched_categories && s.watched_categories.length > 0 && (
                      <> · Categories: {s.watched_categories.join(", ")}</>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => editSetting(s)}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Edit
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
