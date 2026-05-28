"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { FileUpload } from "@/components/file-upload";
import toast from "react-hot-toast";

export default function GeneratePage() {
  const router = useRouter();
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [roleType, setRoleType] = useState("backend");
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  // Auth guard
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setChecking(false);
    }
  }, [router]);

  if (checking) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </main>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobDescription.trim()) {
      toast.error("Job description is required");
      return;
    }
    if (!resumeFile && !resumeText.trim()) {
      toast.error("Provide a resume (file or text)");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("jd_text", jobDescription);
      formData.append("role_type", roleType);
      if (resumeFile) {
        formData.append("resume_file", resumeFile);
      } else {
        formData.append("resume_text", resumeText);
      }

      const res = await apiClient.post("/kits/generate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success("Kit generation started!");
      router.push(`/kit/${res.data.kit_id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-3xl mx-auto py-12 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Generate Interview Kit</h1>
        <button
          onClick={() => router.push("/dashboard")}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          ← Back to Dashboard
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Role Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Role Type</label>
          <select
            value={roleType}
            onChange={(e) => setRoleType(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500"
          >
            <option value="backend">Backend Engineer</option>
            <option value="frontend">Frontend Engineer</option>
            <option value="fullstack">Full Stack Engineer</option>
            <option value="data_engineer">Data Engineer</option>
            <option value="data_scientist">Data Scientist</option>
            <option value="devops">DevOps / SRE</option>
            <option value="ml_engineer">ML Engineer</option>
            <option value="mobile">Mobile Developer</option>
            <option value="engineering_manager">Engineering Manager</option>
          </select>
        </div>

        {/* Job Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Description</label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={8}
            placeholder="Paste the full job description here..."
            className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Resume Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Resume</label>
          <FileUpload onFileSelect={setResumeFile} selectedFile={resumeFile} />
          <p className="text-xs text-gray-500 mt-2">Or paste resume text below:</p>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            rows={4}
            placeholder="Paste resume text here (optional if file uploaded)..."
            className="w-full mt-2 border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Generating..." : "Generate Interview Kit"}
        </button>
      </form>
    </main>
  );
}
