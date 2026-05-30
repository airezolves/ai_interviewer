"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import toast from "react-hot-toast";

type Turn = {
  turn_index: number;
  question: string;
  question_type: string;
  topic: string;
  answer: string | null;
};

type State = {
  session_id: string;
  status: string;
  current_turn_index: number;
  max_turns: number;
  plan: { topics: string[]; rationale: string } | null;
  turns: Turn[];
  next_question: string | null;
  finished: boolean;
};

export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const kitId = params.id as string;
  const [state, setState] = useState<State | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const start = useCallback(async () => {
    try {
      // Try to fetch existing state first
      const existing = await apiClient.get(`/kits/${kitId}/interview`).catch(() => null);
      if (existing?.data?.session_id) {
        setState(existing.data);
        setLoading(false);
        return;
      }
      const res = await apiClient.post(`/kits/${kitId}/interview/start`, { max_turns: 8 });
      setState(res.data);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to start interview");
    } finally {
      setLoading(false);
    }
  }, [kitId]);

  useEffect(() => {
    start();
  }, [start]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state]);

  const submitAnswer = async () => {
    if (!answer.trim() || !state || state.finished) return;
    setSending(true);
    try {
      const res = await apiClient.post(`/kits/${kitId}/interview/answer`, { answer });
      setState(res.data);
      setAnswer("");
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to send answer");
    } finally {
      setSending(false);
    }
  };

  const finalize = async () => {
    setFinalizing(true);
    try {
      await apiClient.post(`/kits/${kitId}/interview/finalize`);
      router.push(`/kit/${kitId}/report`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Finalize failed");
      setFinalizing(false);
    }
  };

  if (loading) return <div className="p-12 text-center text-gray-500">Starting interview…</div>;
  if (!state) return <div className="p-12 text-center text-red-500">No session</div>;

  const visibleTurns = state.turns.filter(t => t.question);
  const currentTopic = visibleTurns[visibleTurns.length - 1]?.topic;

  return (
    <main className="max-w-3xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <Link href={`/kit/${kitId}`} className="text-sm text-brand-600 hover:underline">← Match Summary</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">Live Interview</h1>
          {currentTopic && (
            <p className="text-sm text-gray-500 mt-0.5">Topic: <span className="font-medium">{currentTopic}</span></p>
          )}
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Turn</p>
          <p className="text-lg font-bold text-gray-900">
            {Math.min(state.current_turn_index, state.max_turns)} / {state.max_turns}
          </p>
        </div>
      </div>

      {state.plan?.topics && (
        <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-xs font-medium text-gray-500 mb-1.5">PLAN</p>
          <div className="flex flex-wrap gap-1.5">
            {state.plan.topics.map((t, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded bg-white border border-gray-200 text-gray-700">{t}</span>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 min-h-[400px] max-h-[60vh] overflow-y-auto space-y-4">
        {visibleTurns.map((turn) => (
          <div key={turn.turn_index} className="space-y-2">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold flex-shrink-0">AI</div>
              <div className="flex-1">
                <p className="text-sm text-gray-900 leading-relaxed">{turn.question}</p>
                <p className="text-xs text-gray-400 mt-1">{turn.question_type === "followup" ? "follow-up" : "planned"} · {turn.topic}</p>
              </div>
            </div>
            {turn.answer && (
              <div className="flex gap-3 ml-11">
                <div className="flex-1 bg-gray-50 rounded-lg p-3">
                  <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{turn.answer}</p>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {!state.finished ? (
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                submitAnswer();
              }
            }}
            disabled={sending}
            rows={4}
            placeholder="Type the candidate's answer here… (⌘/Ctrl+Enter to send)"
            className="w-full border-0 focus:ring-0 resize-none text-sm"
          />
          <div className="flex justify-between items-center pt-2 border-t">
            <p className="text-xs text-gray-400">{answer.length} chars</p>
            <button
              onClick={submitAnswer}
              disabled={sending || !answer.trim()}
              className="px-4 py-1.5 bg-brand-600 text-white text-sm rounded-md font-medium hover:bg-brand-700 disabled:opacity-50"
            >
              {sending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-5 text-center">
          <p className="font-semibold text-emerald-900 mb-3">Interview complete.</p>
          <button
            onClick={finalize}
            disabled={finalizing}
            className="px-5 py-2.5 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50"
          >
            {finalizing ? "Generating report…" : "Generate Final Report →"}
          </button>
        </div>
      )}
    </main>
  );
}
