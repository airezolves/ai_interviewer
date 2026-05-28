"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface Kit {
  id: string;
  title: string;
  role_type: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [kits, setKits] = useState<Kit[]>([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(true);

  // Auth guard
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setChecking(false);
    }
  }, [router]);

  useEffect(() => {
    if (!checking) {
      apiClient
        .get("/kits")
        .then((res) => setKits(res.data.kits || []))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [checking]);

  if (checking) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </main>
    );
  }

  return (
    <main className="max-w-5xl mx-auto py-12 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Interview Kits</h1>
        <div className="flex gap-3">
          <Link
            href="/generate"
            className="px-4 py-2 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
          >
            + New Kit
          </Link>
          <button
            onClick={() => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
              router.push("/login");
            }}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : kits.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No kits generated yet.</p>
          <Link href="/generate" className="text-brand-600 hover:underline">
            Generate your first kit
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {kits.map((kit) => (
            <Link
              key={kit.id}
              href={`/kit/${kit.id}`}
              className="block p-6 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{kit.title}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {kit.role_type.replace("_", " ")} •{" "}
                    {new Date(kit.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    kit.status === "complete"
                      ? "bg-green-100 text-green-700"
                      : kit.status === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-yellow-100 text-yellow-700"
                  }`}
                >
                  {kit.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
