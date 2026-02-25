"use client";

import { useState } from "react";
import { DocumentFormData, FormField } from "@/types/chat";

interface DocumentFormProps {
  form: DocumentFormData;
  onSubmit: (docType: string, formData: Record<string, string>) => void;
  disabled?: boolean;
}

export default function DocumentForm({ form, onSubmit, disabled }: DocumentFormProps) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const field of form.fields) {
      initial[field.key] = field.value || "";
    }
    return initial;
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
    onSubmit(form.doc_type, values);
  };

  if (submitted) {
    return (
      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center gap-2 text-green-700 text-sm font-medium">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Podatki poslani — potrdite generiranje dokumenta.
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 border border-navy/10 rounded-lg overflow-hidden">
      <div className="bg-navy/5 px-4 py-2.5 border-b border-navy/10">
        <h4 className="text-sm font-semibold text-navy flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          Dopolni podatke za {form.doc_type}
        </h4>
      </div>
      <div className="p-4 space-y-3 bg-white">
        {form.fields.map((field) => (
          <FieldInput
            key={field.key}
            field={field}
            value={values[field.key] || ""}
            onChange={(v) => handleChange(field.key, v)}
          />
        ))}
        <button
          onClick={handleSubmit}
          disabled={disabled}
          className="w-full mt-2 px-4 py-2.5 bg-navy text-white text-sm font-medium rounded-lg hover:bg-navy/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          Generiraj dokument
        </button>
      </div>
    </div>
  );
}

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormField;
  value: string;
  onChange: (v: string) => void;
}) {
  const baseClass =
    "w-full px-3 py-2 text-sm border border-navy/15 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy/20 focus:border-navy/30 bg-white";

  return (
    <div>
      <label className="block text-xs font-medium text-navy/70 mb-1">
        {field.label}
        {field.required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {field.type === "select" && field.options ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={baseClass}
        >
          <option value="">-- Izberite --</option>
          {field.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : field.type === "textarea" ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          rows={2}
          className={baseClass + " resize-none"}
        />
      ) : field.type === "date" ? (
        <input
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={baseClass}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={baseClass}
        />
      )}
    </div>
  );
}
