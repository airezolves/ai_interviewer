import { useState } from "react";

const PHASES = [
  {
    id: 0,
    name: "Phase 0",
    title: "Validate & Foundation",
    timeline: "Week 1–2",
    color: "#6366F1",
    accent: "#818CF8",
    bg: "#EEF2FF",
    goal: "Prove demand exists before writing a single line of product code.",
    features: [
      {
        name: "Landing Page + Waitlist",
        priority: "P0",
        effort: "2–3 days",
        complexity: "Low",
        description: "Single-page site explaining the value prop with email capture. Paste a sample JD+resume and show a static example output.",
        techNotes: "Next.js static page, Resend or Mailchimp for email capture, deploy on Vercel.",
        why: "Validates demand before building. Target: 200+ sign-ups in 2 weeks."
      },
      {
        name: "Core LLM Prompt R&D",
        priority: "P0",
        effort: "5–7 days",
        complexity: "Medium-High",
        description: "Design and iterate on prompt templates for data science roles: question generation, practical test generation, rubric generation. Test with 10+ real resumes.",
        techNotes: "Anthropic Claude API. Build a local Python script to iterate fast. Version control prompts in Git. Test structured JSON output.",
        why: "The prompt IS the product. If the output quality is mediocre, nothing else matters."
      },
      {
        name: "Resume Parsing Pipeline",
        priority: "P0",
        effort: "3–4 days",
        complexity: "Medium",
        description: "Parse PDF/DOCX resumes into structured text. Extract: skills, experience level, tech stack, projects, education, employment timeline.",
        techNotes: "PyMuPDF for PDF text extraction, python-docx for DOCX. Feed raw text to LLM for structuring. Handle messy formatting gracefully.",
        why: "Resume-aware personalization is the key differentiator vs ChatGPT."
      }
    ]
  },
  {
    id: 1,
    name: "Phase 1",
    title: "Core MVP — The Interview Kit Engine",
    timeline: "Week 3–8",
    color: "#059669",
    accent: "#34D399",
    bg: "#ECFDF5",
    goal: "Ship the core product: JD + Resume → complete interview kit in 60 seconds.",
    features: [
      {
        name: "JD + Resume Input UI",
        priority: "P0",
        effort: "3–4 days",
        complexity: "Low-Medium",
        description: "Two-panel input: paste or upload JD (left), paste or upload resume PDF/DOCX (right). Role type selector (Data Scientist, ML Engineer, Data Analyst, Data Engineer, Analytics Engineer).",
        techNotes: "Next.js + Tailwind. File upload with react-dropzone. Store in Supabase Storage. Client-side PDF text preview.",
        why: "The entry point to the entire product. Must feel instant and frictionless."
      },
      {
        name: "AI Question Generation with Model Answers",
        priority: "P0",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Generate 8–12 tailored questions (behavioral + technical) based on resume-JD match. Each question includes: the question, what it tests, model answer, follow-up probes, difficulty level.",
        techNotes: "Claude API with role-specific prompt templates. Structured JSON output → rendered as interactive cards. Stream response for perceived speed.",
        why: "Core value prop #1. Must be clearly better than pasting into ChatGPT."
      },
      {
        name: "Practical Assessment Generator",
        priority: "P0",
        effort: "7–10 days",
        complexity: "Medium-High",
        description: "Generate a tailored practical test matched to candidate's experience level. Includes: task description, dataset/scenario description, expected deliverables, time limit, evaluation criteria. Three difficulty variants (Junior/Mid/Senior).",
        techNotes: "Hardest feature. Need role-specific templates: data science → EDA + modeling task, ML eng → pipeline design, data eng → ETL challenge. LLM generates within template constraints.",
        why: "THE differentiator. No competitor generates personalized practical tests. This is the wedge."
      },
      {
        name: "Scoring Rubric Generator",
        priority: "P0",
        effort: "3–5 days",
        complexity: "Medium",
        description: "Generate weighted scoring rubric with 6–10 criteria. Each criterion has: name, weight (%), 1-5 scale with calibration examples (what 1/3/5 looks like), and pass/fail threshold.",
        techNotes: "Structured JSON schema enforced via Claude's structured output. Store rubric separately for later candidate comparison feature.",
        why: "Makes evaluation objective. Without this, the tool is just a fancy question bank."
      },
      {
        name: "Candidate Red Flags & Probes",
        priority: "P1",
        effort: "2–3 days",
        complexity: "Low-Medium",
        description: "AI identifies 3–5 potential concerns from resume (gaps, skill mismatches, unclear contributions) with diplomatic probe questions for each.",
        techNotes: "Additional prompt section during resume analysis. Low marginal LLM cost since resume is already parsed.",
        why: "Gives first-time interviewers the intuition of a senior hiring manager."
      },
      {
        name: "Interview Flow Guide",
        priority: "P1",
        effort: "2–3 days",
        complexity: "Low",
        description: "Minute-by-minute interview structure: intro (5 min) → behavioral (15 min) → technical deep-dive (20 min) → practical discussion (15 min) → candidate Q&A (5 min). Maps each generated question to a time slot.",
        techNotes: "Template-based with dynamic question mapping. Simple but high-impact UX addition.",
        why: "Turns a question bank into a complete interview playbook. Huge value for first-time interviewers."
      },
      {
        name: "PDF Export / Printable Kit",
        priority: "P0",
        effort: "3–4 days",
        complexity: "Low-Medium",
        description: "One-click download of the complete interview kit as a clean, printable PDF. Includes all sections: questions, practical test, rubric, red flags, flow guide.",
        techNotes: "Puppeteer server-side rendering or react-pdf. Branded template with your logo. Generate on-demand, cache for 24 hours.",
        why: "Interviewers need this on a second screen or printed. Non-negotiable for usability."
      },
      {
        name: "User Auth + Kit History",
        priority: "P1",
        effort: "3–4 days",
        complexity: "Low-Medium",
        description: "Sign up / login (email + Google OAuth). Dashboard showing all generated kits with search and filter. Kit detail view with edit capability.",
        techNotes: "Supabase Auth (free tier). PostgreSQL for kit storage. Simple dashboard with Next.js server components.",
        why: "Retention mechanism. Users return to review past kits and prep for follow-up interviews."
      },
      {
        name: "Free Tier + Usage Limits",
        priority: "P0",
        effort: "1–2 days",
        complexity: "Low",
        description: "Free: 3 kits/month, no practical test generation. Pro: unlimited kits with full features. Simple paywall with upgrade prompt.",
        techNotes: "Usage counter in Supabase. Stripe Checkout for upgrade (add later). Initially can be manual/honor-system.",
        why: "Acquisition engine. Free tier must be useful enough to build habit."
      }
    ]
  },
  {
    id: 2,
    name: "Phase 2",
    title: "Retention & Team Features",
    timeline: "Week 9–16",
    color: "#D97706",
    accent: "#FBBF24",
    bg: "#FFFBEB",
    goal: "Make the product sticky and unlock team-level revenue.",
    features: [
      {
        name: "Candidate Comparison Dashboard",
        priority: "P1",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Side-by-side comparison of 2–5 candidates for the same role. Normalized scores across rubric criteria. Visual radar chart + ranking table. Hire recommendation with confidence level.",
        techNotes: "Requires all kits for a role to use same rubric schema. D3.js or Recharts for visualization. Comparison algorithm normalizes interviewer scores.",
        why: "Solves 'how do I decide between candidates?' — the final pain point in the hiring workflow."
      },
      {
        name: "Post-Interview Debrief Template",
        priority: "P1",
        effort: "3–4 days",
        complexity: "Low-Medium",
        description: "After the interview, generate a pre-filled debrief form with rubric criteria. Interviewer fills in scores + notes. Produces a standardized evaluation shareable with team.",
        techNotes: "Form generated from stored rubric JSON. Autosave to Supabase. Export as PDF or shareable link.",
        why: "Closes the loop: preparation → interview → evaluation. Makes the product essential to the full workflow."
      },
      {
        name: "Shareable Kit Links",
        priority: "P1",
        effort: "2–3 days",
        complexity: "Low",
        description: "Generate a shareable link to any kit. Co-interviewers can view the kit without an account. Prompted to sign up after viewing.",
        techNotes: "Unique UUID-based public routes. View-only access. Sign-up prompt after 30 seconds.",
        why: "Primary viral loop. Every shared kit is a new potential user."
      },
      {
        name: "Team Workspaces",
        priority: "P2",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Create a team. Invite members. Shared candidate pool. Shared rubric templates. Team-level billing.",
        techNotes: "Supabase RLS (Row Level Security) for multi-tenant data isolation. Invitation system via email. Stripe team billing.",
        why: "Unlocks B2B revenue. Teams pay 3–10x more than individuals."
      },
      {
        name: "Feedback Loop System",
        priority: "P1",
        effort: "2–3 days",
        complexity: "Low",
        description: "After each interview, prompt: 'Were these questions useful? (1–5)' 'Was the practical test appropriate? (Yes/No)' 'Any questions you'd add or remove?' Store feedback for prompt improvement.",
        techNotes: "Simple modal post-interview. Store in feedback table. Aggregate for prompt quality analysis.",
        why: "Your long-term data moat. After 10K kits with feedback, your prompts will be unbeatable."
      },
      {
        name: "Role Template Library",
        priority: "P2",
        effort: "4–5 days",
        complexity: "Medium",
        description: "Pre-built interview templates for 15–20 common technical roles (beyond initial data science). Users can browse, preview, and customize before generating a full kit.",
        techNotes: "Curated prompt templates per role. Community submissions (later). Stored as versioned JSON configs.",
        why: "Expanding beyond data science without compromising quality. Each template is hand-tuned."
      }
    ]
  },
  {
    id: 3,
    name: "Phase 3",
    title: "Growth & Integrations",
    timeline: "Month 5–8",
    color: "#DC2626",
    accent: "#F87171",
    bg: "#FEF2F2",
    goal: "Scale acquisition through SEO, integrations, and API. Target: $10K MRR.",
    features: [
      {
        name: "SEO Interview Question Generator Pages",
        priority: "P1",
        effort: "7–10 days",
        complexity: "Medium",
        description: "Create a free, public interview question generator for every major technical role. Each page targets high-volume keywords ('data scientist interview questions'). CTA to generate a full personalized kit.",
        techNotes: "Programmatic SEO with Next.js ISR. Pre-generated content for 50+ roles. Schema markup for Google rich results.",
        why: "Highest-ROI acquisition channel long-term. These pages compound over months."
      },
      {
        name: "ATS Integration (Greenhouse + Lever)",
        priority: "P2",
        effort: "10–14 days",
        complexity: "Medium-High",
        description: "Connect to Greenhouse/Lever. Auto-pull JD and candidate resume when an interview is scheduled. Push generated kit back as interview prep notes.",
        techNotes: "Greenhouse Harvest API, Lever API. OAuth2 connection flow. Webhook for interview-scheduled events. Marketplace listing.",
        why: "Distribution through ATS marketplaces. Reduces friction to zero: kit auto-generated when interview is booked."
      },
      {
        name: "Calendar Integration",
        priority: "P2",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Connect Google Calendar / Outlook. Detect interview events. Auto-prompt to generate a kit 24 hours before the interview with a notification.",
        techNotes: "Google Calendar API, Microsoft Graph API. Event detection via title keywords ('interview', 'screen', 'technical'). Email/push notification.",
        why: "Habit loop: the tool reaches out to YOU before the interview, not the other way around."
      },
      {
        name: "API for Embedding",
        priority: "P2",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Public API: POST JD + resume → GET interview kit JSON. For ATS platforms, recruiting agencies, and HR tech companies to embed your engine.",
        techNotes: "REST API with API key auth. Rate limiting. Usage-based billing. OpenAPI spec + documentation.",
        why: "B2B2B revenue stream. High margins, no sales effort required per customer."
      },
      {
        name: "Stripe Billing + Plan Management",
        priority: "P1",
        effort: "3–5 days",
        complexity: "Low-Medium",
        description: "Full billing: monthly/annual subscriptions, team billing, usage tracking, invoices, cancellation flow.",
        techNotes: "Stripe Billing + Customer Portal. Webhooks for subscription lifecycle. Usage metering for API tier.",
        why: "Required for scaling revenue beyond manual invoicing."
      },
      {
        name: "Analytics Dashboard (Internal)",
        priority: "P2",
        effort: "3–4 days",
        complexity: "Low-Medium",
        description: "Internal dashboard tracking: kits generated/day, conversion rates, churn, NPS, popular role types, feedback scores. Not user-facing.",
        techNotes: "Simple admin panel with Recharts. Data from Supabase + Stripe. Helps prioritize features based on usage.",
        why: "Data-driven decisions. Know what users actually use vs what you assume they use."
      }
    ]
  },
  {
    id: 4,
    name: "Phase 4",
    title: "Intelligence & Scale",
    timeline: "Month 9–14",
    color: "#7C3AED",
    accent: "#A78BFA",
    bg: "#F5F3FF",
    goal: "Build data moats and advanced features that make the product irreplaceable.",
    features: [
      {
        name: "Prompt Quality Engine (ML-Driven)",
        priority: "P1",
        effort: "10–14 days",
        complexity: "High",
        description: "Use accumulated feedback data to automatically improve prompt templates. A/B test question formats. Track which questions get highest usefulness ratings per role type.",
        techNotes: "Feedback aggregation pipeline. Statistical significance testing for prompt variants. Automated prompt versioning. This is your data moat.",
        why: "After 10K+ kits, your prompts will be measurably better than any competitor starting fresh."
      },
      {
        name: "Interviewer Performance Analytics",
        priority: "P2",
        effort: "7–10 days",
        complexity: "Medium-High",
        description: "Track which interviewers' assessments best predict successful hires (requires hire/no-hire outcome data). Surface calibration insights: 'You tend to score SQL skills higher than your team average.'",
        techNotes: "Requires hire outcome tracking (integration with HRIS or manual input). Statistical correlation analysis. Privacy-sensitive — needs careful UX.",
        why: "Unique insight no competitor offers. Transforms from prep tool to hiring intelligence platform."
      },
      {
        name: "Custom Assessment Builder",
        priority: "P2",
        effort: "7–10 days",
        complexity: "Medium",
        description: "Let users create and save custom practical test templates. Share with team. Community marketplace where top templates are public.",
        techNotes: "Template editor with structured fields. Version control. Rating system for community templates. Revenue share for contributors.",
        why: "Community content moat + reduces reliance on pure LLM generation."
      },
      {
        name: "Multi-Round Interview Planning",
        priority: "P2",
        effort: "5–7 days",
        complexity: "Medium",
        description: "Plan a full interview loop: phone screen → technical round → system design → culture fit → hiring manager final. Each round gets a different kit that builds on previous rounds' findings.",
        techNotes: "Linked kit generation. Pass previous round's debrief data as context to next round's prompt. Prevents question repetition across rounds.",
        why: "Enterprise-grade feature that justifies premium pricing. Solves the multi-round coordination problem."
      },
      {
        name: "Bias Detection & DEI Reporting",
        priority: "P2",
        effort: "5–7 days",
        complexity: "Medium-High",
        description: "Analyze interviewer scoring patterns for potential bias. Flag when scores correlate with non-job-relevant factors. Generate DEI compliance reports.",
        techNotes: "Statistical analysis on scoring data. Anonymized benchmarks. Sensitive UX — frame as 'calibration help' not 'bias accusation'. Legal review required.",
        why: "Growing regulatory requirement. Strong enterprise upsell feature."
      }
    ]
  }
];

const TOTAL_FEATURES = PHASES.reduce((sum, p) => sum + p.features.length, 0);

const priorityColors = {
  "P0": { bg: "#DC2626", text: "#FFF" },
  "P1": { bg: "#D97706", text: "#FFF" },
  "P2": { bg: "#6B7280", text: "#FFF" },
};

const complexityColors = {
  "Low": "#22C55E",
  "Low-Medium": "#84CC16",
  "Medium": "#EAB308",
  "Medium-High": "#F97316",
  "High": "#EF4444",
};

export default function MVPRoadmap() {
  const [activePhase, setActivePhase] = useState(1);
  const [expandedFeature, setExpandedFeature] = useState(null);
  const [view, setView] = useState("roadmap"); // roadmap | technical | verdict

  const phase = PHASES[activePhase];

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#0B0F1A", color: "#E2E8F0", minHeight: "100vh", padding: "24px 20px" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: 3, color: "#6366F1", textTransform: "uppercase", marginBottom: 6 }}>MVP Feature Roadmap</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: "0 0 4px", background: "linear-gradient(135deg, #818CF8, #34D399)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          InterviewKit AI
        </h1>
        <p style={{ fontSize: 13, color: "#94A3B8", margin: 0 }}>AI Interview Preparation Guide Generator for Technical Hiring</p>
      </div>

      {/* View Tabs */}
      <div style={{ display: "flex", justifyContent: "center", gap: 4, marginBottom: 24, background: "#151B2E", borderRadius: 10, padding: 4, maxWidth: 480, margin: "0 auto 24px" }}>
        {[
          { key: "roadmap", label: "Feature Roadmap" },
          { key: "technical", label: "Technical Analysis" },
          { key: "verdict", label: "Verdict & Scoring" },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setView(tab.key)}
            style={{
              flex: 1, padding: "10px 8px", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit",
              background: view === tab.key ? "#6366F1" : "transparent",
              color: view === tab.key ? "#FFF" : "#94A3B8",
              transition: "all 0.2s"
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════ */}
      {/* ROADMAP VIEW */}
      {/* ═══════════════════════════════════════ */}
      {view === "roadmap" && (
        <>
          {/* Phase Selector */}
          <div style={{ display: "flex", gap: 6, marginBottom: 20, overflowX: "auto", paddingBottom: 4 }}>
            {PHASES.map(p => (
              <button
                key={p.id}
                onClick={() => { setActivePhase(p.id); setExpandedFeature(null); }}
                style={{
                  flex: "0 0 auto", padding: "10px 16px", border: `2px solid ${activePhase === p.id ? p.color : "#1E293B"}`,
                  borderRadius: 10, cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600,
                  background: activePhase === p.id ? `${p.color}18` : "#111827",
                  color: activePhase === p.id ? p.accent : "#64748B",
                  transition: "all 0.2s"
                }}
              >
                <div>{p.name}</div>
                <div style={{ fontSize: 10, fontWeight: 400, marginTop: 2, opacity: 0.7 }}>{p.timeline}</div>
              </button>
            ))}
          </div>

          {/* Phase Header */}
          <div style={{ background: `linear-gradient(135deg, ${phase.color}15, ${phase.color}08)`, border: `1px solid ${phase.color}30`, borderRadius: 14, padding: "18px 20px", marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: phase.accent, letterSpacing: 1.5, textTransform: "uppercase" }}>{phase.name} — {phase.timeline}</div>
                <h2 style={{ fontSize: 20, fontWeight: 700, margin: "4px 0", color: "#F1F5F9" }}>{phase.title}</h2>
              </div>
              <div style={{ background: `${phase.color}25`, borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: 600, color: phase.accent }}>
                {phase.features.length} features
              </div>
            </div>
            <p style={{ fontSize: 13, color: "#94A3B8", margin: "8px 0 0", lineHeight: 1.5 }}>{phase.goal}</p>
          </div>

          {/* Feature Cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {phase.features.map((f, idx) => {
              const isExpanded = expandedFeature === `${phase.id}-${idx}`;
              return (
                <div
                  key={idx}
                  onClick={() => setExpandedFeature(isExpanded ? null : `${phase.id}-${idx}`)}
                  style={{
                    background: isExpanded ? "#151B2E" : "#111827",
                    border: `1px solid ${isExpanded ? phase.color + "50" : "#1E293B"}`,
                    borderRadius: 12, padding: "14px 16px", cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                >
                  {/* Feature header row */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 0 }}>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 4,
                        background: priorityColors[f.priority].bg, color: priorityColors[f.priority].text,
                        flexShrink: 0
                      }}>
                        {f.priority}
                      </span>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "#F1F5F9" }}>{f.name}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                      <span style={{ fontSize: 11, color: "#64748B", fontFamily: "'JetBrains Mono', monospace" }}>{f.effort}</span>
                      <span style={{ fontSize: 16, color: "#475569", transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>▾</span>
                    </div>
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid #1E293B" }}>
                      <p style={{ fontSize: 13, color: "#CBD5E1", lineHeight: 1.6, margin: "0 0 12px" }}>{f.description}</p>

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                        <div style={{ background: "#0F172A", borderRadius: 6, padding: "6px 12px", fontSize: 11 }}>
                          <span style={{ color: "#64748B" }}>Complexity: </span>
                          <span style={{ color: complexityColors[f.complexity], fontWeight: 600 }}>{f.complexity}</span>
                        </div>
                        <div style={{ background: "#0F172A", borderRadius: 6, padding: "6px 12px", fontSize: 11 }}>
                          <span style={{ color: "#64748B" }}>Effort: </span>
                          <span style={{ color: "#E2E8F0", fontWeight: 600 }}>{f.effort}</span>
                        </div>
                      </div>

                      <div style={{ background: "#0B0F1A", borderRadius: 8, padding: 12, marginBottom: 10, borderLeft: `3px solid ${phase.color}` }}>
                        <div style={{ fontSize: 10, fontWeight: 600, color: phase.accent, letterSpacing: 1, textTransform: "uppercase", marginBottom: 4 }}>Technical Notes</div>
                        <p style={{ fontSize: 12, color: "#94A3B8", margin: 0, lineHeight: 1.5, fontFamily: "'JetBrains Mono', monospace" }}>{f.techNotes}</p>
                      </div>

                      <div style={{ background: "#0B0F1A", borderRadius: 8, padding: 12, borderLeft: "3px solid #22C55E" }}>
                        <div style={{ fontSize: 10, fontWeight: 600, color: "#34D399", letterSpacing: 1, textTransform: "uppercase", marginBottom: 4 }}>Why This Matters</div>
                        <p style={{ fontSize: 12, color: "#94A3B8", margin: 0, lineHeight: 1.5 }}>{f.why}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Summary Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginTop: 20 }}>
            {[
              { label: "Total Features", value: TOTAL_FEATURES, color: "#6366F1" },
              { label: "P0 (Must Ship)", value: PHASES.reduce((s, p) => s + p.features.filter(f => f.priority === "P0").length, 0), color: "#DC2626" },
              { label: "Total Timeline", value: "~14 months", color: "#059669" },
            ].map((s, i) => (
              <div key={i} style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 10, padding: "14px 12px", textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 10, color: "#64748B", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ═══════════════════════════════════════ */}
      {/* TECHNICAL ANALYSIS VIEW */}
      {/* ═══════════════════════════════════════ */}
      {view === "technical" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Architecture Overview */}
          <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#818CF8", margin: "0 0 12px" }}>System Architecture</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                { layer: "Frontend", tech: "Next.js 14 + Tailwind CSS", notes: "App Router, Server Components, streaming UI" },
                { layer: "Backend", tech: "Next.js API Routes + FastAPI", notes: "FastAPI for AI pipeline, Next.js for auth/CRUD" },
                { layer: "Database", tech: "Supabase (PostgreSQL)", notes: "RLS for multi-tenancy, real-time subscriptions" },
                { layer: "AI Engine", tech: "Claude API (primary)", notes: "Structured output, prompt versioning, fallback to GPT-4" },
                { layer: "Resume Parser", tech: "PyMuPDF + Claude extraction", notes: "PDF → raw text → structured JSON via LLM" },
                { layer: "PDF Generation", tech: "Puppeteer / react-pdf", notes: "Server-side render of interview kit to downloadable PDF" },
                { layer: "Auth", tech: "Supabase Auth", notes: "Email + Google OAuth, JWT sessions" },
                { layer: "Hosting", tech: "Vercel + Railway", notes: "Vercel for frontend, Railway for FastAPI microservice" },
                { layer: "Payments", tech: "Stripe Billing", notes: "Subscriptions, usage metering, Customer Portal" },
                { layer: "Monitoring", tech: "Sentry + PostHog", notes: "Error tracking + product analytics from Day 1" },
              ].map((item, i) => (
                <div key={i} style={{ background: "#0B0F1A", borderRadius: 8, padding: 12, borderLeft: "3px solid #6366F1" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#818CF8", marginBottom: 2 }}>{item.layer}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#E2E8F0", marginBottom: 2 }}>{item.tech}</div>
                  <div style={{ fontSize: 11, color: "#64748B" }}>{item.notes}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Pipeline Detail */}
          <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#34D399", margin: "0 0 12px" }}>AI Pipeline Architecture</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                { step: "1", title: "Input Processing", desc: "Resume PDF/DOCX → PyMuPDF text extraction → LLM structures into { skills, experience, projects, education, gaps }", time: "2–4s" },
                { step: "2", title: "JD Analysis", desc: "Raw JD text → LLM extracts { required_skills, seniority, responsibilities, nice_to_haves, team_context }", time: "1–2s" },
                { step: "3", title: "Match Analysis", desc: "Candidate profile × JD requirements → skill match score, gap identification, experience level calibration", time: "1–2s" },
                { step: "4", title: "Kit Generation", desc: "Parallel generation: questions (5–8s) + practical test (5–8s) + rubric (3–5s) + red flags (2–3s) + flow guide (1–2s)", time: "8–12s" },
                { step: "5", title: "Assembly & Formatting", desc: "JSON outputs → structured kit document → cached in DB → rendered to UI + PDF-ready format", time: "1–2s" },
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", background: "#0B0F1A", borderRadius: 8, padding: 12 }}>
                  <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, #059669, #34D399)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: "#FFF", flexShrink: 0 }}>
                    {item.step}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#E2E8F0" }}>{item.title}</div>
                      <div style={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace", color: "#34D399", background: "#05966915", padding: "2px 8px", borderRadius: 4 }}>{item.time}</div>
                    </div>
                    <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 4, lineHeight: 1.5 }}>{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, background: "#059669" + "15", border: "1px solid #05966930", borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#34D399" }}>Total Generation Time: 15–25 seconds</div>
              <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 2 }}>Perceived as ~10s with streaming UI. Steps 4a–4e run in parallel to minimize wait.</div>
            </div>
          </div>

          {/* Cost Analysis */}
          <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#FBBF24", margin: "0 0 12px" }}>Cost & Infrastructure Analysis</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                { item: "LLM API cost per kit", value: "$0.08–$0.25", note: "Claude Sonnet for most tasks, Opus for complex practical tests" },
                { item: "Infrastructure (MVP stage)", value: "$50–$150/month", note: "Vercel Pro ($20) + Railway ($20–50) + Supabase Free + Domain ($15/yr)" },
                { item: "Infrastructure (1K users)", value: "$300–$600/month", note: "Supabase Pro ($25) + Railway scale + Sentry ($26) + PostHog free tier" },
                { item: "Break-even users (at $39/mo)", value: "~15–20 paying users", note: "Covers infra + LLM costs. Very achievable within first 3 months." },
                { item: "Gross margin at scale", value: "85–92%", note: "SaaS economics are excellent. LLM costs are the only meaningful COGS." },
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0B0F1A", borderRadius: 8, padding: "10px 14px", gap: 8, flexWrap: "wrap" }}>
                  <div style={{ fontSize: 13, color: "#E2E8F0", fontWeight: 500 }}>{item.item}</div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "#FBBF24", fontFamily: "'JetBrains Mono', monospace" }}>{item.value}</div>
                    <div style={{ fontSize: 10, color: "#64748B" }}>{item.note}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Scalability & Security */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 16 }}>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: "#F87171", margin: "0 0 10px" }}>Scalability Challenges</h4>
              {["LLM rate limits during traffic spikes (mitigate: queue + retry)", "PDF generation server load at scale (mitigate: async worker queue)", "Database query optimization for candidate comparison (mitigate: proper indexing, materialized views)", "Prompt versioning across concurrent users (mitigate: immutable prompt configs)"].map((c, i) => (
                <div key={i} style={{ fontSize: 11, color: "#94A3B8", marginBottom: 6, paddingLeft: 12, borderLeft: "2px solid #F8717130", lineHeight: 1.5 }}>{c}</div>
              ))}
            </div>
            <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 16 }}>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: "#818CF8", margin: "0 0 10px" }}>Security Requirements</h4>
              {["HTTPS everywhere + encrypted database (Supabase default)", "Resume data encrypted at rest, auto-delete after 90 days", "LLM provider DPA (Anthropic + OpenAI both offer this)", "No PII in logs or analytics events", "SOC 2 Type I by Month 12 (use Vanta or Drata for automation)", "GDPR compliance from Day 1 (consent, deletion, data export)"].map((c, i) => (
                <div key={i} style={{ fontSize: 11, color: "#94A3B8", marginBottom: 6, paddingLeft: 12, borderLeft: "2px solid #818CF830", lineHeight: 1.5 }}>{c}</div>
              ))}
            </div>
          </div>

          {/* Engineering Bottlenecks */}
          <div style={{ background: "#111827", border: "1px solid #DC262630", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#F87171", margin: "0 0 12px" }}>Potential Engineering Bottlenecks</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                { issue: "Practical test quality consistency", risk: "High", fix: "Role-specific templates with strict constraints. Human QA on first 500 kits." },
                { issue: "Resume parsing edge cases", risk: "Medium", fix: "LLM handles messy text well. Fallback: ask user to paste text manually." },
                { issue: "LLM hallucination in model answers", risk: "Medium", fix: "Constrain answers with rubric criteria. Add disclaimer: 'Suggested answers — calibrate to your context.'" },
                { issue: "Multi-tenant data isolation", risk: "Low", fix: "Supabase RLS handles this natively. Test thoroughly before launch." },
              ].map((b, i) => (
                <div key={i} style={{ background: "#0B0F1A", borderRadius: 8, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#E2E8F0" }}>{b.issue}</div>
                    <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: b.risk === "High" ? "#DC262625" : b.risk === "Medium" ? "#D9770625" : "#05966925", color: b.risk === "High" ? "#F87171" : b.risk === "Medium" ? "#FBBF24" : "#34D399" }}>{b.risk}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#94A3B8", lineHeight: 1.5 }}>{b.fix}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════ */}
      {/* VERDICT VIEW */}
      {/* ═══════════════════════════════════════ */}
      {view === "verdict" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Score Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {[
              { label: "Roadmap Feasibility", score: 8.5, max: 10, color: "#22C55E", desc: "MVP is buildable in 6–8 weeks by a solo data scientist/developer." },
              { label: "Technical Risk", score: 3, max: 10, color: "#22C55E", desc: "Low risk. Standard stack, proven APIs, no novel infrastructure." },
              { label: "Market Timing", score: 9, max: 10, color: "#6366F1", desc: "Perfect timing. Post-AI wave, skills-based hiring trend, quality > quantity." },
              { label: "Competitive Moat (Year 1)", score: 4, max: 10, color: "#EAB308", desc: "Initially weak. Grows with feedback data, templates, and community." },
              { label: "Revenue Potential (Year 1)", score: 6.5, max: 10, color: "#6366F1", desc: "$50K–$150K ARR achievable. Requires strong PLG execution." },
              { label: "Founder-Market Fit", score: 9.5, max: 10, color: "#22C55E", desc: "You ARE the user. Domain expertise + technical ability = rare combo." },
            ].map((s, i) => (
              <div key={i} style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 12, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8" }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color, fontFamily: "'JetBrains Mono', monospace" }}>{s.score}<span style={{ fontSize: 12, color: "#475569" }}>/{s.max}</span></div>
                </div>
                <div style={{ height: 4, background: "#1E293B", borderRadius: 2, marginBottom: 8 }}>
                  <div style={{ height: "100%", width: `${(s.score / s.max) * 100}%`, background: s.color, borderRadius: 2, transition: "width 0.5s ease" }} />
                </div>
                <div style={{ fontSize: 11, color: "#64748B", lineHeight: 1.4 }}>{s.desc}</div>
              </div>
            ))}
          </div>

          {/* Overall Verdict */}
          <div style={{ background: "linear-gradient(135deg, #6366F108, #34D39908)", border: "1px solid #6366F130", borderRadius: 14, padding: 20, textAlign: "center" }}>
            <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: 2, color: "#818CF8", textTransform: "uppercase", marginBottom: 4 }}>Overall Verdict</div>
            <div style={{ fontSize: 48, fontWeight: 700, background: "linear-gradient(135deg, #818CF8, #34D399)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", margin: "4px 0" }}>7.8 / 10</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#22C55E", marginBottom: 8 }}>BUILD IT</div>
            <div style={{ fontSize: 13, color: "#94A3B8", maxWidth: 500, margin: "0 auto", lineHeight: 1.6 }}>
              Strong opportunity with excellent founder-market fit and low entry cost. The roadmap is technically achievable for a solo builder. Primary risk is distribution, not product.
            </div>
          </div>

          {/* Phase-by-Phase Scoring */}
          <div style={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#E2E8F0", margin: "0 0 14px" }}>Phase-by-Phase Risk Assessment</h3>
            {PHASES.map((p, i) => {
              const riskScores = [
                { feasibility: 95, risk: "Very Low", milestone: "200+ waitlist sign-ups" },
                { feasibility: 85, risk: "Low-Medium", milestone: "100 users, 300+ kits generated" },
                { feasibility: 70, risk: "Medium", milestone: "50 paying teams, 30% retention" },
                { feasibility: 60, risk: "Medium-High", milestone: "$10K+ MRR, ATS integration live" },
                { feasibility: 50, risk: "High", milestone: "Data moat established, $30K+ MRR" },
              ];
              const rs = riskScores[i];
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: i < PHASES.length - 1 ? 12 : 0, paddingBottom: i < PHASES.length - 1 ? 12 : 0, borderBottom: i < PHASES.length - 1 ? "1px solid #1E293B" : "none" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: p.color, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#E2E8F0" }}>{p.name}: {p.title}</div>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 4,
                        background: rs.risk.includes("Very Low") || rs.risk === "Low-Medium" ? "#05966920" : rs.risk === "Medium" ? "#D9770620" : "#DC262620",
                        color: rs.risk.includes("Very Low") || rs.risk === "Low-Medium" ? "#34D399" : rs.risk === "Medium" ? "#FBBF24" : "#F87171"
                      }}>{rs.risk} Risk</span>
                    </div>
                    <div style={{ height: 4, background: "#1E293B", borderRadius: 2, marginBottom: 4 }}>
                      <div style={{ height: "100%", width: `${rs.feasibility}%`, background: p.color, borderRadius: 2 }} />
                    </div>
                    <div style={{ fontSize: 11, color: "#64748B" }}>Success Metric: {rs.milestone}</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Critical Success Factors */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={{ background: "#111827", border: "1px solid #22C55E30", borderRadius: 14, padding: 16 }}>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: "#34D399", margin: "0 0 10px" }}>What Makes This Roadmap Win</h4>
              {[
                "Start data-science-only → nail quality before expanding",
                "Practical test generation is the unkillable wedge feature",
                "Free tier → viral sharing → team upgrade = natural PLG",
                "Feedback loop from Day 1 builds an unreplicable data moat",
                "Solo-builder-friendly: no feature requires a team to build",
                "Low burn rate: $100–$300/mo infra until 1K users",
              ].map((c, i) => (
                <div key={i} style={{ fontSize: 11, color: "#94A3B8", marginBottom: 6, paddingLeft: 12, borderLeft: "2px solid #22C55E30", lineHeight: 1.5 }}>{c}</div>
              ))}
            </div>
            <div style={{ background: "#111827", border: "1px solid #DC262630", borderRadius: 14, padding: 16 }}>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: "#F87171", margin: "0 0 10px" }}>What Could Derail This Roadmap</h4>
              {[
                "Scope creep: building Phase 3 features during Phase 1",
                "Quality gap: if output feels 'ChatGPT-level', users won't pay",
                "Distribution: great product with no users = failure",
                "Solo burnout: 14-month roadmap is long for one person",
                "ATS adds basic AI questions (commoditizes simplest features)",
                "Underpricing: charging too little delays sustainability",
              ].map((c, i) => (
                <div key={i} style={{ fontSize: 11, color: "#94A3B8", marginBottom: 6, paddingLeft: 12, borderLeft: "2px solid #F8717130", lineHeight: 1.5 }}>{c}</div>
              ))}
            </div>
          </div>

          {/* Final Recommendation */}
          <div style={{ background: "#111827", border: "1px solid #6366F130", borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#818CF8", margin: "0 0 12px" }}>Final Recommendation</h3>
            <div style={{ fontSize: 13, color: "#CBD5E1", lineHeight: 1.7 }}>
              <p style={{ margin: "0 0 10px" }}>
                <strong style={{ color: "#34D399" }}>Ship Phase 0 + Phase 1 in 8 weeks.</strong> That's your entire validation cycle. If 100 users generate 300+ kits and 30%+ return for a second kit, you have product-market fit. If not, you've invested 8 weeks — not 14 months.
              </p>
              <p style={{ margin: "0 0 10px" }}>
                <strong style={{ color: "#FBBF24" }}>Do NOT build Phases 2–4 until Phase 1 metrics are hit.</strong> Every feature in Phases 2–4 is an optimization on a working engine. Building them without a proven engine is wasted effort.
              </p>
              <p style={{ margin: 0 }}>
                <strong style={{ color: "#818CF8" }}>Your unfair advantage is being the user.</strong> Every decision — which questions to generate, what a good practical test looks like, how to score a candidate — benefits from your lived experience as a data scientist who interviews. Trust that intuition. Build fast. Ship ugly. Iterate based on what real users tell you.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
