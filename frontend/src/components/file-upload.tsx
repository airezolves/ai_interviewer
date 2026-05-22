"use client";

import { useRef } from "react";

interface FileUploadProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export function FileUpload({ onFileSelect, selectedFile }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
      if (!allowed.includes(file.type)) {
        alert("Only PDF and DOCX files are supported");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert("File must be under 10MB");
        return;
      }
    }
    onFileSelect(file);
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-brand-500 transition-colors"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        onChange={handleChange}
        className="hidden"
      />
      {selectedFile ? (
        <div>
          <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
          <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600">Click to upload resume (PDF or DOCX)</p>
          <p className="text-xs text-gray-400 mt-1">Max 10MB</p>
        </div>
      )}
    </div>
  );
}
