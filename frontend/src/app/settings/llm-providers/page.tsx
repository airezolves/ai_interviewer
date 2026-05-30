"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import toast from "react-hot-toast";

type Provider = {
  id: string;
  provider: string;
  model: string;
  display_name: string | null;
  endpoint: string | null;
  api_key_masked: string;
  is_active: boolean;
  created_at: string;
};

const PROVIDERS = [
  { value: "gemini", label: "Google Gemini", defaultModel: "gemini-2.5-pro" },
  { value: "openai", label: "OpenAI", defaultModel: "gpt-4o" },
  { value: "anthropic", label: "Anthropic Claude", defaultModel: "claude-sonnet-4-20250514" },
  { value: "deepseek", label: "DeepSeek", defaultModel: "deepseek-chat" },
  { value: "azure", label: "Azure OpenAI", defaultModel: "gpt-4o" },
  { value: "openai-compatible", label: "OpenAI-compatible (local/self-hosted)", defaultModel: "" },
];

export default function LLMProvidersPage() {
  const router = useRouter();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [provider, setProvider] = useState("gemini");
  const [model, setModel] = useState("gemini-2.5-pro");
  const [endpoint, setEndpoint] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("access_token")) {
      router.push("/login");
    }
  }, [router]);

  const fetchProviders = useCallback(async () => {
    try {
      const res = await apiClient.get("/llm-providers");
      setProviders(res.data);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to load providers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const handleProviderChange = (slug: string) => {
    setProvider(slug);
    const p = PROVIDERS.find((x) => x.value === slug);
    setModel(p?.defaultModel || "");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) {
      toast.error("API key is required");
      return;
    }
    if (!model.trim()) {
      toast.error("Model is required");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/llm-providers", {
        provider,
        model,
        endpoint: endpoint.trim() || null,
        api_key: apiKey,
        is_active: true,
      });
      toast.success("Provider added & activated");
      setShowForm(false);
      setApiKey("");
      setEndpoint("");
      await fetchProviders();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to add provider");
    } finally {
      setSubmitting(false);
    }
  };

  const activate = async (id: string) => {
    try {
      await apiClient.post(`/llm-providers/${id}/activate`);
      toast.success("Activated");
      await fetchProviders();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Activation failed");
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Delete this provider?")) return;
    try {
      await apiClient.delete(`/llm-providers/${id}`);
      toast.success("Deleted");
      await fetchProviders();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <main className="max-w-3xl mx-auto py-10 px-4">
      <Link href="/dashboard" className="text-sm text-brand-600 hover:underline">← Dashboard</Link>
      <div className="flex justify-between items-center mt-1 mb-2">
        <h1 className="text-3xl font-bold text-gray-900">LLM Providers</h1>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700"
          >
            + Add Provider
          </button>
        )}
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Plug in your own API key. Keys are AES-256-GCM encrypted at rest. Exactly one provider is active at a time.
      </p>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gemini-2.5-pro, gpt-4o, claude-sonnet-4"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            />
          </div>

          {(provider === "azure" || provider === "openai-compatible") && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint URL</label>
              <input
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                placeholder="https://your-endpoint/v1"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-… / AIza… / ..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
              autoComplete="new-password"
            />
            <p className="text-xs text-gray-400 mt-1">Stored encrypted. Only the last 4 chars are shown after save.</p>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-2 bg-brand-600 text-white rounded-md font-medium hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? "Saving…" : "Save & Activate"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="text-center text-gray-500 py-12">Loading…</div>
      ) : providers.length === 0 ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <p className="text-amber-900 font-medium mb-1">No LLM provider configured.</p>
          <p className="text-sm text-amber-800">You must add one before generating kits.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {providers.map((p) => (
            <div
              key={p.id}
              className={`bg-white border rounded-lg p-4 flex items-center justify-between ${
                p.is_active ? "border-brand-400 ring-1 ring-brand-200" : "border-gray-200"
              }`}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900 capitalize">{p.provider}</span>
                  <span className="text-sm text-gray-500">·</span>
                  <span className="text-sm text-gray-700">{p.model}</span>
                  {p.is_active && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">ACTIVE</span>
                  )}
                </div>
                <p className="text-xs text-gray-400 font-mono mt-0.5">{p.api_key_masked}</p>
                {p.endpoint && <p className="text-xs text-gray-500 mt-0.5">{p.endpoint}</p>}
              </div>
              <div className="flex gap-2">
                {!p.is_active && (
                  <button
                    onClick={() => activate(p.id)}
                    className="px-3 py-1.5 text-sm border border-brand-300 text-brand-700 rounded-md hover:bg-brand-50"
                  >
                    Activate
                  </button>
                )}
                <button
                  onClick={() => remove(p.id)}
                  className="px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-md hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
