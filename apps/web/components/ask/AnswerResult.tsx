"use client";

import React, { useState } from "react";
import { ShieldCheck, AlertCircle, Copy, Check } from "lucide-react";
import { QueryAnswer } from "@/lib/api";
import { EvidenceCard } from "@/components/interview/EvidenceCard";

interface AnswerResultProps {
  result: QueryAnswer;
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const AnswerResult: React.FC<AnswerResultProps> = ({
  result,
  onPlayTimestamp,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(result.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sourcesCount = result.evidence.length;

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-200">
      {/* Grounding Meta Visualizer Strip */}
      <section className="w-full py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 font-label-code text-label-code border-b border-border">
        <div className="flex items-center gap-2 text-on-surface min-w-0">
          <span className="text-secondary shrink-0">QUERY:</span>
          <span className="font-medium truncate">&ldquo;{result.query}&rdquo;</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-surface-container-high text-primary font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            {sourcesCount} {sourcesCount === 1 ? "Citation" : "Citations"} Grounded
          </span>

          {result.has_sufficient_evidence ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Grounded &amp; Verified</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Insufficient Evidence Safeguard</span>
            </span>
          )}
        </div>
      </section>

      {/* Core Workbench Area (Asymmetric Grid) */}
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Synthesis (Left Column) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="bg-surface-container-lowest rounded-xl p-5 border border-border shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>

            <div className="flex items-center justify-between gap-3 mb-3 pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-primary text-white font-label-sm text-label-sm tracking-wider uppercase">
                  AI Synthesis
                </span>
                <span className="font-label-code text-label-code text-secondary">
                  Grounded RAG Extraction
                </span>
              </div>

              <button
                type="button"
                onClick={handleCopy}
                className="p-1 rounded hover:bg-surface-container text-secondary hover:text-on-surface transition-colors cursor-pointer inline-flex items-center gap-1 text-xs font-label-code"
                title="Copy synthesis"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700 font-medium">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>

            {/* Answer Text */}
            <div className="font-body-md text-body-md text-on-surface leading-relaxed whitespace-pre-line space-y-2">
              {result.answer}
            </div>

            {/* If Insufficient Evidence, Display Explicit Guardrail Box */}
            {!result.has_sufficient_evidence && (
              <div className="mt-4 p-3.5 rounded-lg bg-surface-container-low border border-amber-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-label-sm font-semibold text-amber-900">
                  <span>STATE: INSUFFICIENT EVIDENCE SAFEGUARD TRIGGERED</span>
                </div>
                <p className="font-body-sm text-body-sm text-amber-950 bg-surface-container-lowest p-2 rounded border border-border font-medium">
                  &ldquo;There is not enough evidence in the provided interviews to answer this confidently.&rdquo;
                </p>
                <p className="font-label-code text-[11px] text-secondary">
                  The synthesis engine suppresses speculative completions when source transcripts do not corroborate the premise.
                </p>
              </div>
            )}

            {/* Themes Detected Chips */}
            {result.themes_detected && result.themes_detected.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border flex flex-wrap items-center gap-1.5">
                <span className="font-label-code text-[11px] text-secondary mr-1">
                  Corroborated Themes:
                </span>
                {result.themes_detected.map((thm, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-code text-[11px] border border-border/60"
                  >
                    {thm}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Supporting Evidence Canvas (Right Column) */}
        <div className="lg:col-span-5 flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary">
                SUPPORTING EVIDENCE
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface font-label-code text-label-code font-semibold">
                {result.evidence.length} Quotes
              </span>
            </div>
            <span className="font-label-code text-label-code text-secondary text-xs">
              Aligned to audio
            </span>
          </div>

          {result.evidence.length === 0 ? (
            <div className="p-5 rounded-xl border border-dashed border-border bg-surface-container-low text-center text-secondary font-label-code text-xs">
              No direct transcript evidence matches found for this specific query.
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {result.evidence.map((ev, i) => (
                <EvidenceCard
                  key={`${ev.segment_id}-${i}`}
                  evidence={ev}
                  label={`Citation 0${i + 1} · Grounded Source`}
                  onPlayTimestamp={onPlayTimestamp}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
