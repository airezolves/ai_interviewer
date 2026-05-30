"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import toast from "react-hot-toast";

type FinalReport = {
  overall_score: number;
  dimension_scores: {
    technical: number;
    communication: number;
    problem_solving: number;
    role_fit: number;
    culture_alignment: number;
  };
  pros: string[];
  cons: string[];
  role_suitability: string;
  recommendation: string;
  reasoning: string;
};

type Kit = { id: string; title: string | null; role_type: string; final_analysis: FinalReport | null };

const REC: Record<string, { label: string; color: string }> = {
  hire: { label: "HIRE", color: "bg-emerald-600" },
  maybe: { label: "MAYBE", color: "bg-amber-500" },
  no_hire: { label: "NO HIRE", color: "bg-red-600" },
};

function Bar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 55 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="mb-2.5">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="font-bold text-gray-900">{pct.toFixed(0)}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function ReportPage() {
  const params = useParams();
  const kitId = params.id as string;
  const [kit, setKit] = useState<Kit | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get(`/kits/${kitId}`)
      .then((r) => setKit(r.data))
      .catch(() => toast.error("Failed to load report"))
      .finally(() => setLoading(false));
  }, [kitId]);

  if (loading) return <div className="p-12 text-center text-gray-500">Loading report…</div>;
  if (!kit?.final_analysis) {
    return (
      <main className="max-w-3xl mx-auto py-12 px-4 text-center">
        <p className="text-gray-700 mb-4">No final analysis yet.</p>
        <Link href={`/kit/${kitId}/interview`} className="text-brand-600 hover:underline">Continue interview</Link>
      </main>
    );
  }

  const r = kit.final_analysis;
  const rec = REC[r.recommendation] || { label: r.recommendation, color: "bg-gray-500" };

  return (
    <main className="max-w-3xl mx-auto py-10 px-4">
      <Link href={`/kit/${kitId}`} className="text-sm text-brand-600 hover:underline">← Back to kit</Link>
      <h1 className="text-3xl font-bold text-gray-900 mt-1 mb-6">{kit.title || "Final Report"}</h1>

      <section className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Overall</p>
            <p className="text-5xl font-bold text-gray-900 mt-1">{r.overall_score.toFixed(1)}</p>
          </div>
          <span className={`px-4 py-2 text-white font-bold rounded-md ${rec.color}`}>{rec.label}</span>
        </div>

        <div className="grid md:grid-cols-2 gap-x-8">
          <Bar label="Technical" value={r.dimension_scores.technical} />
          <Bar label="Communication" value={r.dimension_scores.communication} />
          <Bar label="Problem Solving" value={r.dimension_scores.problem_solving} />
          <Bar label="Role Fit" value={r.dimension_scores.role_fit} />
          <Bar label="Culture Alignment" value={r.dimension_scores.culture_alignment} />
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">Role Suitability</h2>
        <p className="text-sm text-gray-700 leading-relaxed">{r.role_suitability}</p>
      </section>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <section className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Pros</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            {r.pros.map((p, i) => (
              <li key={i} className="flex gap-2"><span className="text-emerald-500">✓</span><span>{p}</span></li>
            ))}
          </ul>
        </section>
        <section className="bg-white border border-gray-200 rounded-lg p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Cons</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            {r.cons.map((c, i) => (
              <li key={i} className="flex gap-2"><span className="text-red-400">!</span><span>{c}</span></li>
            ))}
          </ul>
        </section>
      </div>

      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="font-semibold text-gray-900 mb-3">Detailed Reasoning</h2>
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{r.reasoning}</p>
      </section>
    </main>
  );
}
