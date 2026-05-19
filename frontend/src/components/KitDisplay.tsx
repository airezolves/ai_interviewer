'use client';

import { useState } from 'react';

interface KitDisplayProps {
  kit: any;
  onBack: () => void;
}

type Tab = 'questions' | 'assessment' | 'rubric' | 'red_flags' | 'flow_guide';

export function KitDisplay({ kit, onBack }: KitDisplayProps) {
  const [activeTab, setActiveTab] = useState<Tab>('questions');

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'questions', label: 'Questions', icon: '❓' },
    { key: 'assessment', label: 'Assessment', icon: '📋' },
    { key: 'rubric', label: 'Rubric', icon: '📊' },
    { key: 'red_flags', label: 'Red Flags', icon: '🚩' },
    { key: 'flow_guide', label: 'Flow Guide', icon: '🗺️' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <button
            onClick={onBack}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium mb-2"
          >
            ← Generate New Kit
          </button>
          <h2 className="text-2xl font-bold text-slate-900">Interview Kit Generated</h2>
          {kit.jd_analysis && (
            <p className="text-slate-500 text-sm mt-1">
              {kit.jd_analysis.role_title} • {kit.jd_analysis.seniority_level} level
            </p>
          )}
        </div>
        <button className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 font-medium text-sm">
          Download PDF
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        {activeTab === 'questions' && <QuestionsSection data={kit.questions} />}
        {activeTab === 'assessment' && <AssessmentSection data={kit.assessment} />}
        {activeTab === 'rubric' && <RubricSection data={kit.rubric} />}
        {activeTab === 'red_flags' && <RedFlagsSection data={kit.red_flags} />}
        {activeTab === 'flow_guide' && <FlowGuideSection data={kit.flow_guide} />}
      </div>
    </div>
  );
}

function QuestionsSection({ data }: { data: any }) {
  if (!data?.questions) return <EmptyState section="questions" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900">Interview Questions ({data.questions.length})</h3>
      {data.questions.map((q: any, idx: number) => (
        <div key={idx} className="border border-slate-100 rounded-xl p-4 hover:shadow-sm transition-shadow">
          <div className="flex items-start gap-3">
            <span className="flex-shrink-0 w-7 h-7 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-bold">
              {idx + 1}
            </span>
            <div className="flex-1">
              <p className="font-medium text-slate-900">{q.question}</p>
              <div className="flex gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  q.category === 'behavioral' ? 'bg-purple-100 text-purple-700' :
                  q.category === 'technical' ? 'bg-blue-100 text-blue-700' :
                  'bg-orange-100 text-orange-700'
                }`}>
                  {q.category}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  q.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                  q.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {q.difficulty}
                </span>
                <span className="text-xs text-slate-400">{q.tests}</span>
              </div>
              <div className="mt-3 bg-green-50 border-l-3 border-green-400 p-3 rounded-r-lg">
                <p className="text-xs font-medium text-green-700 mb-1">Model Answer:</p>
                <p className="text-sm text-slate-700">{q.model_answer}</p>
              </div>
              {q.follow_ups && (
                <div className="mt-2 text-xs text-slate-500">
                  <span className="font-medium">Follow-ups:</span> {q.follow_ups.join(' • ')}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AssessmentSection({ data }: { data: any }) {
  if (!data?.assessments) return <EmptyState section="assessment" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900">Practical Assessment</h3>
      {data.recommended_level && (
        <p className="text-sm text-primary-600 font-medium">
          Recommended Level: {data.recommended_level.toUpperCase()}
        </p>
      )}
      {data.assessments.map((a: any, idx: number) => (
        <div key={idx} className="border border-slate-100 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className={`text-xs font-bold px-2 py-1 rounded ${
              a.level === 'junior' ? 'bg-green-100 text-green-700' :
              a.level === 'mid' ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>
              {a.level?.toUpperCase()}
            </span>
            <h4 className="font-semibold text-slate-900">{a.title}</h4>
          </div>
          <p className="text-sm text-slate-600 mb-3">{a.description}</p>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-slate-700">Time Limit</p>
              <p className="text-slate-500">{a.time_limit}</p>
            </div>
            {a.deliverables && (
              <div>
                <p className="font-medium text-slate-700">Deliverables</p>
                <ul className="text-slate-500 list-disc list-inside">
                  {a.deliverables.map((d: string, i: number) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function RubricSection({ data }: { data: any }) {
  if (!data?.criteria) return <EmptyState section="rubric" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900">Scoring Rubric</h3>
      {data.pass_threshold && (
        <div className="flex gap-4 text-sm">
          <span className="text-slate-500">Pass: <strong className="text-amber-600">{data.pass_threshold}/5</strong></span>
          <span className="text-slate-500">Strong Hire: <strong className="text-green-600">{data.strong_hire_threshold}/5</strong></span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-primary-50">
              <th className="text-left p-3 rounded-tl-lg">Criterion</th>
              <th className="p-3 w-16">Weight</th>
              <th className="p-3">1 (Poor)</th>
              <th className="p-3">3 (Adequate)</th>
              <th className="p-3 rounded-tr-lg">5 (Exceptional)</th>
            </tr>
          </thead>
          <tbody>
            {data.criteria.map((c: any, idx: number) => (
              <tr key={idx} className="border-b border-slate-100">
                <td className="p-3">
                  <p className="font-medium text-slate-900">{c.name}</p>
                  <p className="text-xs text-slate-400">{c.description}</p>
                </td>
                <td className="p-3 text-center font-bold text-primary-600">{c.weight}%</td>
                <td className="p-3 text-xs text-slate-500">{c.scale?.['1']}</td>
                <td className="p-3 text-xs text-slate-500">{c.scale?.['3']}</td>
                <td className="p-3 text-xs text-slate-500">{c.scale?.['5']}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RedFlagsSection({ data }: { data: any }) {
  if (!data?.red_flags) return <EmptyState section="red flags" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900">Red Flags & Probes</h3>
        {data.overall_risk_level && (
          <span className={`text-xs font-bold px-3 py-1 rounded-full ${
            data.overall_risk_level === 'low' ? 'bg-green-100 text-green-700' :
            data.overall_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            {data.overall_risk_level.toUpperCase()} RISK
          </span>
        )}
      </div>
      {data.red_flags.map((rf: any, idx: number) => (
        <div key={idx} className="bg-red-50 border-l-4 border-red-400 rounded-r-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${
              rf.severity === 'high' ? 'bg-red-200 text-red-800' :
              rf.severity === 'medium' ? 'bg-amber-200 text-amber-800' :
              'bg-slate-200 text-slate-700'
            }`}>
              {rf.severity?.toUpperCase()}
            </span>
            <span className="text-xs text-slate-500">{rf.category?.replace('_', ' ')}</span>
          </div>
          <p className="font-medium text-slate-900 text-sm">{rf.flag}</p>
          <p className="text-xs text-slate-500 mt-1">Evidence: {rf.evidence}</p>
          {rf.probe_questions && (
            <div className="mt-2">
              <p className="text-xs font-medium text-red-700">Probe Questions:</p>
              <ul className="text-xs text-slate-600 list-disc list-inside mt-1">
                {rf.probe_questions.map((pq: string, i: number) => (
                  <li key={i}>{pq}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function FlowGuideSection({ data }: { data: any }) {
  if (!data?.sections) return <EmptyState section="flow guide" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-900">
        Interview Flow Guide ({data.total_duration} min)
      </h3>
      <div className="space-y-3">
        {data.sections.map((s: any, idx: number) => (
          <div key={idx} className="flex gap-4 items-start">
            <div className="flex-shrink-0 w-16 text-right">
              <span className="text-xs font-mono font-bold text-green-600">
                {s.start_minute}–{s.start_minute + s.duration_minutes}m
              </span>
            </div>
            <div className="w-px h-full bg-green-200 self-stretch" />
            <div className="flex-1 bg-green-50 border border-green-100 rounded-lg p-3">
              <h4 className="font-medium text-slate-900 text-sm">{s.name}</h4>
              <p className="text-xs text-slate-600 mt-1">{s.purpose}</p>
              {s.tips && (
                <p className="text-xs text-green-700 mt-2">💡 {s.tips.join(' | ')}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {data.pre_interview_checklist && (
        <div className="mt-6 bg-slate-50 rounded-xl p-4">
          <h4 className="font-medium text-slate-900 text-sm mb-2">Pre-Interview Checklist</h4>
          <ul className="text-xs text-slate-600 space-y-1">
            {data.pre_interview_checklist.map((item: string, i: number) => (
              <li key={i} className="flex items-center gap-2">
                <input type="checkbox" className="rounded border-slate-300" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EmptyState({ section }: { section: string }) {
  return (
    <div className="text-center py-12 text-slate-400">
      <p>No {section} data available. The generation might have encountered an issue.</p>
    </div>
  );
}
