'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '@/lib/api';

interface KitInputProps {
  onGenerate: (kit: any) => void;
  loading: boolean;
  setLoading: (v: boolean) => void;
}

const ROLE_TYPES = [
  { value: 'data_scientist', label: 'Data Scientist' },
  { value: 'ml_engineer', label: 'ML Engineer' },
  { value: 'data_analyst', label: 'Data Analyst' },
  { value: 'data_engineer', label: 'Data Engineer' },
  { value: 'analytics_engineer', label: 'Analytics Engineer' },
  { value: 'software_engineer', label: 'Software Engineer' },
  { value: 'backend_engineer', label: 'Backend Engineer' },
  { value: 'frontend_engineer', label: 'Frontend Engineer' },
  { value: 'fullstack_engineer', label: 'Full Stack Engineer' },
];

export function KitInput({ onGenerate, loading, setLoading }: KitInputProps) {
  const [jdText, setJdText] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [roleType, setRoleType] = useState('data_scientist');
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setResumeFile(acceptedFiles[0]);
      setResumeText('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const handleGenerate = async () => {
    if (!jdText.trim()) {
      setError('Please paste a job description');
      return;
    }
    if (!resumeText.trim() && !resumeFile) {
      setError('Please paste resume text or upload a file');
      return;
    }

    setError('');
    setLoading(true);

    try {
      let parsedResume: any;

      // Parse resume
      if (resumeFile) {
        const formData = new FormData();
        formData.append('file', resumeFile);
        const parseResp = await apiClient.parseResumeFile(formData);
        parsedResume = parseResp.structured_data;
      } else {
        const parseResp = await apiClient.parseResumeText(resumeText);
        parsedResume = parseResp.data;
      }

      // Generate full kit
      const kitResp = await apiClient.generateKit({
        jd_text: jdText,
        resume_data: parsedResume,
        role_type: roleType,
      });

      onGenerate(kitResp.data);
    } catch (err: any) {
      setError(err.message || 'Failed to generate kit. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">
          Generate Your Interview Kit
        </h2>
        <p className="text-slate-600 max-w-xl mx-auto">
          Paste a job description and resume to get a personalized interview guide with questions, 
          practical assessments, scoring rubrics, and more.
        </p>
      </div>

      {/* Role Type Selector */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">Role Type</label>
        <div className="flex flex-wrap gap-2">
          {ROLE_TYPES.map((role) => (
            <button
              key={role.value}
              onClick={() => setRoleType(role.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                roleType === role.value
                  ? 'bg-primary-500 text-white shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {role.label}
            </button>
          ))}
        </div>
      </div>

      {/* Two-panel Input */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* JD Panel */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Job Description
          </label>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the full job description here..."
            className="w-full h-64 p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
          />
          <p className="text-xs text-slate-400 mt-1">{jdText.length} characters</p>
        </div>

        {/* Resume Panel */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Resume
          </label>

          {/* File Upload */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors mb-3 ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-slate-200 hover:border-primary-300'
            }`}
          >
            <input {...getInputProps()} />
            {resumeFile ? (
              <div className="text-sm text-green-600 font-medium">
                ✓ {resumeFile.name}
                <button
                  onClick={(e) => { e.stopPropagation(); setResumeFile(null); }}
                  className="ml-2 text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div>
                <p className="text-sm text-slate-500">
                  Drop PDF/DOCX here or click to upload
                </p>
                <p className="text-xs text-slate-400 mt-1">Max 10MB</p>
              </div>
            )}
          </div>

          {/* Or paste text */}
          <div className="text-center text-xs text-slate-400 mb-2">— or paste text —</div>
          <textarea
            value={resumeText}
            onChange={(e) => { setResumeText(e.target.value); setResumeFile(null); }}
            placeholder="Paste resume text here..."
            className="w-full h-36 p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
            disabled={!!resumeFile}
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Generate Button */}
      <div className="text-center">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="px-8 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating Kit...
            </span>
          ) : (
            'Generate Interview Kit ✨'
          )}
        </button>
        <p className="text-xs text-slate-400 mt-2">Takes 15-25 seconds</p>
      </div>
    </div>
  );
}
