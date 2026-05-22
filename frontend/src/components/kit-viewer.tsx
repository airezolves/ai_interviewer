"use client";

interface KitViewerProps {
  kit: {
    match_analysis: any;
    questions: any[];
    practical_test: any;
    rubric: any;
    red_flags: any[];
    flow_guide: any[];
  };
}

export function KitViewer({ kit }: KitViewerProps) {
  return (
    <div className="space-y-8">
      {/* Match Analysis */}
      {kit.match_analysis && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Match Analysis</h2>
          <div className="text-center mb-4">
            <span className="text-4xl font-bold text-green-600">
              {kit.match_analysis.overall_match_score}%
            </span>
            <p className="text-sm text-gray-500">Overall Match</p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Strengths</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {kit.match_analysis.skill_matches?.map((s: string, i: number) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Gaps</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {kit.match_analysis.skill_gaps?.map((g: string, i: number) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    {g}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Questions */}
      {kit.questions?.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Interview Questions ({kit.questions.length})</h2>
          <div className="space-y-4">
            {kit.questions.map((q: any, i: number) => (
              <details key={i} className="border border-gray-100 rounded-lg p-4 hover:bg-gray-50">
                <summary className="cursor-pointer font-medium text-gray-900">
                  {i + 1}. {q.question}
                  <span className="ml-2 text-xs px-2 py-0.5 rounded bg-brand-100 text-brand-700">
                    {q.category}
                  </span>
                </summary>
                <div className="mt-3 text-sm text-gray-600 space-y-2">
                  <p><strong>Tests:</strong> {q.what_it_tests}</p>
                  <p><strong>Difficulty:</strong> {q.difficulty}</p>
                  <div className="bg-green-50 border border-green-200 rounded p-3">
                    <strong>Model Answer:</strong> {q.model_answer}
                  </div>
                </div>
              </details>
            ))}
          </div>
        </section>
      )}

      {/* Practical Test */}
      {kit.practical_test && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Practical Assessment</h2>
          <p className="text-gray-600 mb-4">{kit.practical_test.overview}</p>
          {kit.practical_test.variants?.map((v: any, i: number) => (
            <div key={i} className="border border-gray-100 rounded-lg p-4 mb-3">
              <h4 className="font-medium capitalize">{v.difficulty} — {v.time_limit}</h4>
              <p className="text-sm text-gray-600 mt-2">{v.task_description}</p>
            </div>
          ))}
        </section>
      )}

      {/* Rubric */}
      {kit.rubric?.criteria && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Scoring Rubric</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3">Criterion</th>
                  <th className="text-left p-3">Weight</th>
                  <th className="text-left p-3">1 (Poor)</th>
                  <th className="text-left p-3">3 (Adequate)</th>
                  <th className="text-left p-3">5 (Excellent)</th>
                </tr>
              </thead>
              <tbody>
                {kit.rubric.criteria.map((c: any, i: number) => (
                  <tr key={i} className="border-t">
                    <td className="p-3 font-medium">{c.name}</td>
                    <td className="p-3">{c.weight_pct}%</td>
                    <td className="p-3 text-gray-600">{c.score_1}</td>
                    <td className="p-3 text-gray-600">{c.score_3}</td>
                    <td className="p-3 text-gray-600">{c.score_5}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Red Flags */}
      {kit.red_flags?.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Red Flags & Probes</h2>
          <div className="space-y-3">
            {kit.red_flags.map((f: any, i: number) => (
              <div key={i} className="border-l-4 border-amber-400 bg-amber-50 rounded-r-lg p-4">
                <p className="text-xs font-bold uppercase text-amber-700">{f.severity} concern</p>
                <p className="font-medium text-gray-900 mt-1">{f.concern}</p>
                <p className="text-sm text-gray-600 mt-1"><em>Probe:</em> {f.probe_question}</p>
                <p className="text-xs text-gray-500 mt-1">Listen for: {f.what_to_listen_for}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Flow Guide */}
      {kit.flow_guide?.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Interview Flow Guide</h2>
          <div className="space-y-3">
            {kit.flow_guide.map((step: any, i: number) => (
              <div key={i} className="flex gap-4 items-start">
                <div className="text-sm font-bold text-brand-600 min-w-[40px]">
                  {step.duration_minutes}m
                </div>
                <div>
                  <p className="font-medium text-gray-900">{step.section}</p>
                  <p className="text-sm text-gray-500">{step.activities?.join(" → ")}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
