"use client";

import { API_BASE_URL } from "../../lib/api";

import React, { useState } from "react";
import { UploadCloud, CheckCircle2, AlertCircle, FileText, Loader2 } from "lucide-react";

interface UploadFormProps {
  onSuccess?: () => void;
  apiBaseUrl?: string;
  schoolEmail?: string | null;
}

export const UploadForm: React.FC<UploadFormProps> = ({
  onSuccess,
  apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || API_BASE_URL,
  // apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "${API_BASE_URL}",
  schoolEmail,
}) => {
  const [email, setEmail] = useState(schoolEmail || "");
  const [studentIdFile, setStudentIdFile] = useState<File | null>(null);
  const [admissionFile, setAdmissionFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const MAX_SIZE_MB = 5;
  const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/webp"];

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Invalid type for file ${file.name}. Only PDF, JPG, PNG, and WEBP are allowed.`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File ${file.name} is larger than ${MAX_SIZE_MB}MB.`;
    }
    return null;
  };

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: React.Dispatch<React.SetStateAction<File | null>>
  ) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      setter(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!studentIdFile || !admissionFile) {
      setError("Please select both your Student ID and Admission Letter documents.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      if (email.trim()) formData.append("university_email", email.trim());
      formData.append("student_id", studentIdFile);
      formData.append("admission_letter", admissionFile);

      const token = typeof window !== "undefined" ? localStorage.getItem("campusos_auth_token") : null;
      const response = await fetch(`${apiBaseUrl}/verification/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error?.message || data?.detail || "Verification upload failed.");
      }

      setSuccess("Your verification documents have been submitted successfully! An administrator will review your credentials shortly.");
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || "Failed to upload verification documents.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 sm:p-8 rounded-xl border border-slate-200 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">
        Upload Student Verification Documents
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        To obtain your Verified Student Badge and unlock CampusOS commerce (+10 Trust Score), please provide your official university email and upload scanned copies of your student credentials.
      </p>

      {error && (
        <div className="mt-4 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-4 p-4 rounded-lg bg-emerald-50 border border-emerald-200 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
          <p className="text-sm text-emerald-800">{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            University Institutional Email (optional — uses your profile school email if blank)
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="e.g., amina.bello@unijos.edu.ng"
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <p className="mt-1 text-xs text-slate-500">
            Must belong to a recognized African university academic domain (e.g., .edu.ng, .edu).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Student ID Upload */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Student ID Card (Front/Back)
            </label>
            <div className="flex justify-center rounded-lg border border-dashed border-slate-300 px-6 py-8 hover:border-primary-500 transition-colors">
              <div className="text-center">
                <UploadCloud className="mx-auto h-10 w-10 text-slate-400" />
                <div className="mt-4 flex text-sm leading-6 text-slate-600">
                  <label
                    htmlFor="student-id-file"
                    className="relative cursor-pointer rounded-md bg-white font-semibold text-primary-600 focus-within:outline-none hover:text-primary-500"
                  >
                    <span>Upload a file</span>
                    <input
                      id="student-id-file"
                      name="student-id-file"
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp"
                      className="sr-only"
                      onChange={(e) => handleFileChange(e, setStudentIdFile)}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs leading-5 text-slate-500">PDF, PNG, JPG up to 5MB</p>
                {studentIdFile && (
                  <p className="mt-2 text-xs font-semibold text-emerald-600 flex items-center justify-center gap-1">
                    <CheckCircle2 className="h-4 w-4" /> {studentIdFile.name}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Admission Letter Upload */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              University Admission Letter
            </label>
            <div className="flex justify-center rounded-lg border border-dashed border-slate-300 px-6 py-8 hover:border-primary-500 transition-colors">
              <div className="text-center">
                <FileText className="mx-auto h-10 w-10 text-slate-400" />
                <div className="mt-4 flex text-sm leading-6 text-slate-600">
                  <label
                    htmlFor="admission-letter-file"
                    className="relative cursor-pointer rounded-md bg-white font-semibold text-primary-600 focus-within:outline-none hover:text-primary-500"
                  >
                    <span>Upload admission letter</span>
                    <input
                      id="admission-letter-file"
                      name="admission-letter-file"
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp"
                      className="sr-only"
                      onChange={(e) => handleFileChange(e, setAdmissionFile)}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs leading-5 text-slate-500">PDF, PNG, JPG up to 5MB</p>
                {admissionFile && (
                  <p className="mt-2 text-xs font-semibold text-emerald-600 flex items-center justify-center gap-1">
                    <CheckCircle2 className="h-4 w-4" /> {admissionFile.name}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Uploading Documents..." : "Submit Verification Request"}
          </button>
        </div>
      </form>
    </div>
  );
};
