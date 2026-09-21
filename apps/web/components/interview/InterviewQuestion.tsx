"use client";

import React from "react";
import { Sparkles } from "lucide-react";
import { GuideQuestionAnalysis, EvidenceItem } from "@/lib/api";
import { EvidenceCard } from "./EvidenceCard";

interface InterviewQuestionProps {
  question: GuideQuestionAnalysis;
  index: number;
  hideQuotes?: boolean;
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const InterviewQuestion: React.FC<InterviewQuestionProps> = ({
  question,
  index,
  hideQuotes = false,
  onPlayTimestamp,
}) => {
  // Collect all supporting evidence across experts
  const allEvidence: EvidenceItem[] = question.expert_answers.flatMap(
    (ea) => ea.evidence || []
  );

  const formattedIndex = String(index + 1).padStart(2, "0");

  return (
    <article
      id={`question-${question.question_id}`}
      className="research-item rounded-lg bg-surface-container-lowest border border-border overflow-hidden transition-all shadow-xs"
    >
      {/* Section Header */}
      <div className="p-4 sm:p-5 flex items-start gap-3 border-b border-border bg-surface-container-lowest">
        <div className="shrink-0 w-8 h-8 rounded bg-surface-container-high flex items-center justify-center font-label-code text-label-code text-on-surface font-semibold">
          {formattedIndex}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1 text-xs">
            <span className="font-label-code text-label-code text-secondary uppercase tracking-wider">
              Question {question.question_id}
            </span>
            <span className="text-secondary font-label-code">·</span>
            <span className="font-label-code text-label-code text-primary font-medium">
              3 Markets (FR · DE · UK)
            </span>
          </div>
          <h2 className="font-headline-sm text-headline-sm text-on-surface leading-snug">
            {question.question}
          </h2>
        </div>
      </div>

      {/* Content Body */}
      <div className="p-4 sm:p-5 flex flex-col gap-4">
        {/* AI Synthesis Box */}
        <div className="rounded-lg bg-surface-container-low/70 border border-border/80 p-4 flex flex-col gap-2.5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-primary/10 text-primary font-label-code text-label-code font-semibold tracking-wide">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              AI SYNTHESIS
            </span>
            <span className="font-label-code text-label-code text-secondary">
              Extracted across 3 expert interviews
            </span>
          </div>

          <p className="font-body-md text-body-md text-on-surface leading-relaxed">
            {question.synthesized_answer}
          </p>

          {/* Common Themes & Contrasts if present */}
          {(question.common_themes?.length > 0 ||
            question.contrasting_viewpoints?.length > 0) && (
            <div className="mt-1 pt-2.5 border-t border-border/60 flex flex-wrap gap-2">
              {question.common_themes?.map((t, i) => (
                <span
                  key={`th-${i}`}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white text-primary border border-border font-label-code text-[11px]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  {t}
                </span>
              ))}
              {question.contrasting_viewpoints?.map((c, i) => (
                <span
                  key={`cv-${i}`}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-tertiary-fixed/40 text-tertiary border border-tertiary/20 font-label-code text-[11px]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Supporting Evidence List */}
        <div className="flex flex-col gap-3 pt-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary">
                SUPPORTING EVIDENCE
              </span>
              <span className="px-1.5 py-0.5 rounded bg-surface-container font-label-code text-label-code text-on-surface-variant font-medium">
                ({allEvidence.length} Citations)
              </span>
            </div>
            <span className="font-label-code text-label-code text-secondary hidden sm:inline">
              Click timestamp to play stream
            </span>
          </div>

          <div className="flex flex-col gap-2.5">
            {allEvidence.map((ev, evIdx) => (
              <EvidenceCard
                key={`${ev.segment_id}-${evIdx}`}
                evidence={ev}
                compact={true}
                hideQuote={hideQuotes}
                onPlayTimestamp={onPlayTimestamp}
              />
            ))}
          </div>
        </div>
      </div>
    </article>
  );
};
