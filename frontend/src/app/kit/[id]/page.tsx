"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import toast from "react-hot-toast";

type Dim = { score: number; reasoning: string };
type MatchAnalysis = {
  overall_score: number;
  recommendation: string;
  technical_match: Dim;
  experience_match: Dim;
  skills_match: Dim;
  education_match: Dim;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  gaps: string[];
  summary: string;
};

type Kit = {
  id: string;
  title: string | null;
  role_type: string;
  status: string;
  match_analysis: MatchAnalysis | null;
  proceed_decision: string | null;
  final_analysis: any | null;
};

const REC_LABEL: Record<string, { text: string; color: string }> = {
  strong_proceed: { text: "Strong Match", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  proceed: { text: "Proceed", color: "bg-green-100 text-green-800 border-green-300" },
  borderline: { text: "Borderline", color: "bg-amber-100 text-amber-800 border-amber-300" },
  deny: { text: "Deny", color: "bg-red-100 text-red-800 border-red-300" },
};

function ScoreBar({ label, dim }: { label: string; dim: Dim }) {
  const pct = Math.max(0, Math.min(100, dim.score));
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 55 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="font-semibold text-gray-900">{pct.toFixed(0)}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-gray-500 mt-1">{dim.reasoning}</p>
    </div>
  );
}

export default function KitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const kitId = params.id as string;
  const [kit, setKit] = useState<Kit | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  const fetchKit = useCallback(async () => {
    try {
      const res = await apiClient.get(`/kits/${kitId}`);
      setKit(res.data);
    } catch {
      toast.error("Failed to load kit");
    } finally {
      setLoading(false);
    }
  }, [kitId]);

  useEffect(() => {
    fetchKit();
  }, [fetchKit]);

  // Poll while pipeline is in flight
  useEffect(() => {
    if (!kit) return;
    if (kit.status === "matching" || kit.status === "pending") {
      const t = setInterval(fetchKit, 2500);
      return () => clearInterval(t);
    }
  }, [kit, fetchKit]);

  const handleDecision = async (decision: "proceed" | "denied") => {
    setActing(true);
    try {
      await apiClient.post(`/kits/${kitId}/proceed`, { decision });
      if (decision === "proceed") {
        router.push(`/kit/${kitId}/interview`);
      } else {
        toast.success("Candidate denied.");
        await fetchKit();
      }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Action failed");
    } finally {
      setActing(false);
    }
  };

  if (loading) return <div className="p-12 text-center text-gray-500">Loading...</div>;
  if (!kit) return <div className="p-12 text-center text-red-500">Kit not found</div>;

  const ma = kit.match_analysis;
  const inFlight = kit.status === "matching" || kit.status === "pending";
  const ready = kit.status === "match_ready";
  const decided = !!kit.proceed_decision;

  return (
    <main className="max-w-4xl mx-auto py-10 px-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Link href="/dashboard" className="text-sm text-brand-600 hover:underline">← Dashboard</Link>
          <h1 className="text-3xl font-bold text-gray-900 mt-1">{kit.title || "Interview Kit"}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {kit.role_type.replace("_", " ")} • <span className="font-medium">{kit.status}</span>
          </p>
        </div>
        {kit.final_analysis && (
          <Link
            href={`/kit/${kitId}/report`}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700"
          >
            View Final Report
          </Link>
        )}
      </div>

      {inFlight && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-center">
          <div className="inline-block animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mb-3" />
          <p className="text-blue-900 font-medium">Running match analysis…</p>
          <p className="text-sm text-blue-700 mt-1">Structuring resume, analyzing JD, and computing fit score.</p>
        </div>
      )}

      {kit.status === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
          <p className="text-red-900 font-medium">Match pipeline failed.</p>
          <p className="text-sm text-red-700 mt-1">Check that you have an active LLM provider configured in <Link href="/settings/llm-providers" className="underline">Settings</Link>.</p>
        </div>
      )}

      {ma && (
        <section className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500">Overall Match</p>
              <p className="text-5xl font-bold text-gray-900 mt-1">{ma.overall_score.toFixed(1)}</p>
            </div>
            <span className={`px-3 py-1 text-sm font-semibold rounded-full border ${REC_LABEL[ma.recommendation]?.color || "bg-gray-100 text-gray-700"}`}>
              {REC_LABEL[ma.recommendation]?.text || ma.recommendation}
            </span>
          </div>

          <p className="text-sm text-gray-700 leading-relaxed mb-6">{ma.summary}</p>

          <div className="grid md:grid-cols-2 gap-x-8 gap-y-2 mb-6">
            <ScoreBar label="Technical" dim={ma.technical_match} />
            <ScoreBar label="Experience" dim={ma.experience_match} />
            <ScoreBar label="Skills" dim={ma.skills_match} />
            <ScoreBar label="Education" dim={ma.education_match} />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Strengths</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {ma.strengths.map((s, i) => (
                  <li key={i} className="flex gap-2"><span className="text-emerald-500">✓</span><span>{s}</span></li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Gaps</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {ma.gaps.map((g, i) => (
                  <li key={i} className="flex gap-2"><span className="text-red-400">!</span><span>{g}</span></li>
                ))}
              </ul>
            </div>
          </div>

          {ma.matched_skills?.length > 0 && (
            <div className="mt-6 pt-4 border-t">
              <h4 className="text-xs uppercase tracking-wide text-gray-500 mb-2">Matched skills</h4>
              <div className="flex flex-wrap gap-2">
                {ma.matched_skills.map((s, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 rounded">{s}</span>
                ))}
              </div>
            </div>
          )}
          {ma.missing_skills?.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs uppercase tracking-wide text-gray-500 mb-2">Missing skills</h4>
              <div className="flex flex-wrap gap-2">
                {ma.missing_skills.map((s, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded">{s}</span>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {ready && !decided && (
        <div className="bg-white border-2 border-brand-300 rounded-lg p-6 sticky bottom-4 shadow-lg">
          <h3 className="font-semibold text-gray-900 mb-1">Proceed to interview?</h3>
          <p className="text-sm text-gray-600 mb-4">
            Continue with a live AI-driven interview, or deny this candidate based on the match summary above.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => handleDecision("proceed")}
              disabled={acting}
              className="flex-1 py-2.5 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50"
            >
              {acting ? "..." : "Proceed to Interview →"}
            </button>
            <button
              onClick={() => handleDecision("denied")}
              disabled={acting}
              className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50"
            >
              Deny Candidate
            </button>
          </div>
        </div>
      )}

      {decided && kit.proceed_decision === "proceed" && !kit.final_analysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <Link href={`/kit/${kitId}/interview`} className="font-semibold text-blue-900 hover:underline">
            Resume interview →
          </Link>
        </div>
      )}

      {decided && kit.proceed_decision === "denied" && (
        <div className="bg-gray-100 border border-gray-200 rounded-lg p-4 text-center text-gray-700">
          Candidate denied at match stage.
        </div>
      )}
    </main>
  );
}
