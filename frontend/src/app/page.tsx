"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function HomePage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsAuthenticated(true);
      // Redirect authenticated users to dashboard
      router.push("/dashboard");
    } else {
      setLoading(false);
    }
  }, [router]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold text-gray-900 mb-6 tracking-tight">
              AI-Powered Interview Kits
              <span className="block text-brand-600 mt-2">In Minutes, Not Hours</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
              Transform hiring with comprehensive, personalized interview preparation kits.
              Upload a resume, paste a job description, and get tailored questions, assessments, and scoring rubrics instantly.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                href="/login"
                className="px-8 py-4 bg-brand-600 text-white text-lg font-semibold rounded-xl hover:bg-brand-700 shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5"
              >
                Get Started Free →
              </Link>
              <Link
                href="/login"
                className="px-8 py-4 border-2 border-brand-600 text-brand-700 text-lg font-semibold rounded-xl hover:bg-brand-50 transition-all"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>

        {/* Decorative background elements */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-brand-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Everything You Need to Conduct Great Interviews</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive interview kits powered by advanced AI, tailored to your exact requirements
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-brand-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">15-20 Personalized Questions</h3>
              <p className="text-gray-600">
                AI-generated questions across 6 categories: technical depth, behavioral, system design, problem-solving, domain knowledge, and gap verification.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Skill-Based Practical Tests</h3>
              <p className="text-gray-600">
                5-8 key technical skills assessed with junior, mid, and senior level questions for comprehensive evaluation.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Objective Scoring Rubric</h3>
              <p className="text-gray-600">
                Weighted criteria with detailed score levels for fair, consistent candidate evaluation across all interviews.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Red Flag Detection</h3>
              <p className="text-gray-600">
                Automatically identifies concerns in resumes with diplomatic probe questions to verify candidate claims.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Interview Flow Guide</h3>
              <p className="text-gray-600">
                Minute-by-minute structured interview plan with question mapping, timing, and interviewer tips for smooth execution.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-2xl border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Match Analysis</h3>
              <p className="text-gray-600">
                Detailed compatibility report between candidate skills and job requirements with seniority calibration.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Generate professional interview kits in 3 simple steps</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-brand-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload & Input</h3>
              <p className="text-gray-600">
                Upload candidate's resume (PDF/DOCX) and paste the job description. Select the role type.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-brand-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI Generation</h3>
              <p className="text-gray-600">
                Our AI analyzes both documents and generates personalized questions, tests, and rubrics in minutes.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-brand-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Export & Interview</h3>
              <p className="text-gray-600">
                Review your complete kit, export to PDF, share with team, and conduct a structured interview.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Roles Supported Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Supports All Technical Roles</h2>
            <p className="text-xl text-gray-600">Tailored kits for every engineering position</p>
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            {[
              'Backend Engineer',
              'Frontend Engineer',
              'Full Stack Engineer',
              'Data Engineer',
              'Data Scientist',
              'ML Engineer',
              'DevOps / SRE',
              'Mobile Developer',
              'Engineering Manager'
            ].map((role) => (
              <div
                key={role}
                className="px-6 py-3 bg-gradient-to-r from-brand-50 to-purple-50 border border-brand-200 rounded-full text-brand-700 font-medium hover:shadow-md transition-all"
              >
                {role}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-brand-600 to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Transform Your Hiring Process?
          </h2>
          <p className="text-xl text-brand-100 mb-8">
            Join teams conducting better, faster, and more consistent interviews
          </p>
          <Link
            href="/login"
            className="inline-block px-8 py-4 bg-white text-brand-600 text-lg font-semibold rounded-xl hover:bg-gray-100 shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5"
          >
            Start Generating Kits Now →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-2">InterviewKit AI</h3>
            <p className="text-sm">AI-powered interview preparation for modern hiring teams</p>
            <p className="text-xs mt-4">© 2026 InterviewKit AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
