export interface User {
  id: string;
  email: string;
  full_name: string;
  tier: "free" | "pro" | "enterprise";
  kits_generated_this_month: number;
}

export interface Kit {
  id: string;
  title: string;
  role_type: string;
  status: "pending" | "processing" | "complete" | "partial" | "failed";
  match_analysis: MatchAnalysis | null;
  questions: Question[];
  practical_test: PracticalTest | null;
  rubric: Rubric | null;
  red_flags: RedFlag[];
  flow_guide: FlowStep[];
  created_at: string;
}

export interface MatchAnalysis {
  overall_match_score: number;
  skill_matches: string[];
  skill_gaps: string[];
  experience_assessment: string;
}

export interface Question {
  question: string;
  category: "technical" | "behavioral" | "system_design";
  difficulty: "easy" | "medium" | "hard";
  what_it_tests: string;
  model_answer: string;
}

export interface PracticalTest {
  title: string;
  overview: string;
  variants: {
    difficulty: string;
    time_limit: string;
    task_description: string;
    evaluation_criteria: string[];
  }[];
}

export interface Rubric {
  criteria: {
    name: string;
    weight_pct: number;
    score_1: string;
    score_3: string;
    score_5: string;
  }[];
  pass_threshold: number;
}

export interface RedFlag {
  concern: string;
  severity: "low" | "medium" | "high";
  probe_question: string;
  what_to_listen_for: string;
}

export interface FlowStep {
  section: string;
  duration_minutes: number;
  activities: string[];
}
