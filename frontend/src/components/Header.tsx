'use client';

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-green flex items-center justify-center">
            <span className="text-white font-bold text-sm">IK</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">InterviewKit AI</h1>
            <p className="text-xs text-slate-500">AI-Powered Interview Preparation</p>
          </div>
        </div>

        <nav className="flex items-center gap-4">
          <button className="text-sm text-slate-600 hover:text-primary-600 font-medium">
            My Kits
          </button>
          <button className="text-sm bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 font-medium transition-colors">
            Sign In
          </button>
        </nav>
      </div>
    </header>
  );
}
