import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center max-w-2xl">
        <h1 className="text-5xl font-bold text-brand-600 mb-4">InterviewKit AI</h1>
        <p className="text-xl text-gray-600 mb-8">
          Generate comprehensive, AI-powered interview preparation kits in minutes.
          Upload a resume, paste a job description, and get tailored questions, scoring rubrics,
          practical tests, and more.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/generate"
            className="px-6 py-3 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
          >
            Generate Kit
          </Link>
          <Link
            href="/dashboard"
            className="px-6 py-3 border border-brand-300 text-brand-700 rounded-lg font-medium hover:bg-brand-50 transition-colors"
          >
            My Kits
          </Link>
        </div>
      </div>
    </main>
  );
}
