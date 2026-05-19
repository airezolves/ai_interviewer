export interface Question {
  question: string;
  category: 'behavioral' | 'technical' | 'situational';
  tests: string;
  difficulty: 'easy' | 'medium' | 'hard';
  model_answer: string;
  follow_ups: string[];
  red_flags: string;
  green_flags: string;
}

export interface Assessment {
  level: 'junior' | 'mid' | 'senior';
  title: string;
  description: string;
  dataset_description: string;
  deliverables: string[];
  time_limit: string;
  evaluation_criteria: string[];
  bonus_challenges: string[];
  tools_allowed: string[];
}

export interface RubricCriterion {
  name: string;
  weight: number;
  description: string;
  scale: { '1': string; '3': string; '5': string };
  must_have_signals: string[];
  disqualifying_signals: string[];
}

export interface RedFlag {
  flag: string;
  severity: 'low' | 'medium' | 'high';
  category: string;
  evidence: string;
  probe_questions: string[];
  mitigating_factors: string;
}

export interface FlowSection {
  name: string;
  duration_minutes: number;
  start_minute: number;
  purpose: string;
  questions_to_ask: string[];
  tips: string[];
  transition: string;
}

export interface InterviewKit {
  jd_analysis: {
    role_title: string;
    seniority_level: string;
    required_skills: string[];
    nice_to_haves: string[];
    responsibilities: string[];
    team_context: string;
  };
  questions: { questions: Question[] };
  assessment: { assessments: Assessment[]; recommended_level: string };
  rubric: { criteria: RubricCriterion[]; pass_threshold: number; strong_hire_threshold: number };
  red_flags: { red_flags: RedFlag[]; overall_risk_level: string; summary: string };
  flow_guide: {
    total_duration: number;
    sections: FlowSection[];
    pre_interview_checklist: string[];
    dos_and_donts: { dos: string[]; donts: string[] };
  };
}
