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

// Parse skill-based test structure from markdown-formatted text
function parseSkillBasedTest(taskDescription: string) {
  const skills: Array<{ name: string; questions: Array<{ number: number; text: string; metadata: string }> }> = [];
  
  // Normalize escaped newlines (\\n) to actual newlines
  // This handles both properly formatted strings and JSON-escaped strings
  const normalized = taskDescription.replace(/\\n/g, '\n');
  const lines = normalized.split('\n');
  
  let currentSkill: { name: string; questions: Array<{ number: number; text: string; metadata: string }> } | null = null;
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    
    // Match skill headers like "**Python** (2 questions):"
    const skillMatch = trimmedLine.match(/^\*\*(.+?)\*\*\s*\((\d+)\s+questions?\):?$/);
    if (skillMatch) {
      if (currentSkill) skills.push(currentSkill);
      currentSkill = { name: skillMatch[1], questions: [] };
      continue;
    }
    
    // Match question lines like "1. Write a function..."
    const questionMatch = trimmedLine.match(/^(\d+)\.\s+(.+)/);
    if (questionMatch && currentSkill) {
      currentSkill.questions.push({
        number: parseInt(questionMatch[1]),
        text: questionMatch[2],
        metadata: ''
      });
      continue;
    }
    
    // Match metadata lines like "Time: 10 minutes | Tests: Basic syntax"
    const metadataMatch = trimmedLine.match(/^Time:\s*(.+?)\s*\|\s*Tests:\s*(.+)/);
    if (metadataMatch && currentSkill && currentSkill.questions.length > 0) {
      const lastQuestion = currentSkill.questions[currentSkill.questions.length - 1];
      lastQuestion.metadata = `${metadataMatch[1]} • ${metadataMatch[2]}`;
    }
  }
  
  if (currentSkill) skills.push(currentSkill);
  return skills;
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
          {kit.match_analysis.experience_fit && (
            <div className="mt-4 pt-4 border-t">
              <h4 className="font-medium text-gray-700 mb-2">Experience Assessment</h4>
              <p className="text-sm text-gray-600">{kit.match_analysis.experience_fit}</p>
              <p className="text-xs text-gray-500 mt-1">
                Calibration: <span className="font-semibold capitalize">{kit.match_analysis.level_calibration}</span>
              </p>
            </div>
          )}
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
                  <span className="ml-2 text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                    {q.difficulty}
                  </span>
                </summary>
                <div className="mt-3 text-sm text-gray-600 space-y-2">
                  <p><strong>Tests:</strong> {q.what_it_tests}</p>
                  <div className="bg-green-50 border border-green-200 rounded p-3">
                    <strong className="text-green-900">Model Answer:</strong>
                    <p className="mt-1">{q.model_answer}</p>
                  </div>
                  {q.follow_up_probes?.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-3">
                      <strong className="text-blue-900">Follow-up Probes:</strong>
                      <ul className="mt-1 list-disc list-inside space-y-1">
                        {q.follow_up_probes.map((probe: string, pi: number) => (
                          <li key={pi}>{probe}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {q.relevance_rationale && (
                    <div className="bg-amber-50 border border-amber-200 rounded p-3">
                      <strong className="text-amber-900">Why This Question:</strong>
                      <p className="mt-1">{q.relevance_rationale}</p>
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        </section>
      )}

      {/* Practical Test */}
      {kit.practical_test && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Practical Technical Assessment</h2>
          <p className="text-gray-600 mb-6">{kit.practical_test.overview}</p>
          
          {kit.practical_test.variants?.map((variant: any, vi: number) => {
            const skills = parseSkillBasedTest(variant.task_description);
            const difficultyColors = {
              junior: 'bg-green-100 text-green-800 border-green-300',
              mid: 'bg-blue-100 text-blue-800 border-blue-300',
              senior: 'bg-purple-100 text-purple-800 border-purple-300'
            };
            const colorClass = difficultyColors[variant.difficulty as keyof typeof difficultyColors] || 'bg-gray-100 text-gray-800';
            
            return (
              <div key={vi} className={`border-2 rounded-lg p-5 mb-4 ${colorClass}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold capitalize">
                    {variant.difficulty} Level
                  </h3>
                  <span className="text-sm font-medium px-3 py-1 bg-white rounded-full">
                    ⏱ {variant.time_limit}
                  </span>
                </div>
                
                {skills.length > 0 ? (
                  <div className="space-y-4">
                    {skills.map((skill, si) => (
                      <div key={si} className="bg-white rounded-lg p-4 border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-brand-500 text-white text-xs flex items-center justify-center">
                            {si + 1}
                          </span>
                          {skill.name}
                          <span className="text-xs font-normal text-gray-500">
                            ({skill.questions.length} questions)
                          </span>
                        </h4>
                        <div className="space-y-3 ml-8">
                          {skill.questions.map((q, qi) => (
                            <div key={qi} className="text-sm">
                              <p className="font-medium text-gray-800">{q.number}. {q.text}</p>
                              {q.metadata && (
                                <p className="text-xs text-gray-600 mt-1 italic">{q.metadata}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                      {variant.task_description}
                    </pre>
                  </div>
                )}
                
                <div className="mt-4 pt-4 border-t border-white/50">
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong className="text-gray-900">Expected Deliverables:</strong>
                      <ul className="mt-1 list-disc list-inside text-gray-700">
                        {variant.expected_deliverables?.map((d: string, di: number) => (
                          <li key={di}>{d}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <strong className="text-gray-900">Evaluation Criteria:</strong>
                      <ul className="mt-1 list-disc list-inside text-gray-700">
                        {variant.evaluation_criteria?.slice(0, 5).map((c: string, ci: number) => (
                          <li key={ci}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
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
