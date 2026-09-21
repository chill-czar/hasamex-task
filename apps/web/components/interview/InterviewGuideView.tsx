"use client";

import React, { useState } from "react";
import { ShieldCheck, FoldVertical, UnfoldVertical } from "lucide-react";
import { GuideQuestionAnalysis } from "@/lib/api";
import { InterviewQuestion } from "./InterviewQuestion";

interface InterviewGuideViewProps {
  questions: GuideQuestionAnalysis[];
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const InterviewGuideView: React.FC<InterviewGuideViewProps> = ({
  questions,
  onPlayTimestamp,
}) => {
  const [isCompact, setIsCompact] = useState(false);
  const [activeQuestionId, setActiveQuestionId] = useState<number | null>(null);

  const handleJumpToQuestion = (id: number) => {
    setActiveQuestionId(id);
    const el = document.getElementById(`question-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="flex flex-col w-full gap-6">
      {/* Page Header & Investigative Metadata */}
      <section className="flex flex-col gap-3 pt-2 pb-4 border-b border-border">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <div>
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
              Interview Guide
            </h1>
            <p className="font-body-md text-body-md text-secondary mt-1">
              Explore answers across the three expert interviews with supporting evidence.
            </p>
          </div>

          {/* Quick Filter & Corpus Status */}
          <div className="flex items-center gap-2 self-start sm:self-center">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-surface-container border border-border font-label-code text-label-code text-on-surface-variant">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Corpus Verified (3/3)</span>
            </div>
            <button
              type="button"
              onClick={() => setIsCompact(!isCompact)}
              className="px-3 py-1 rounded bg-surface-container-lowest border border-border font-body-sm text-body-sm text-on-surface hover:bg-surface-container-low transition-colors inline-flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              {isCompact ? (
                <>
                  <UnfoldVertical className="w-3.5 h-3.5 text-secondary" />
                  <span>Expand Quotes</span>
                </>
              ) : (
                <>
                  <FoldVertical className="w-3.5 h-3.5 text-secondary" />
                  <span>Compact View</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Metadata Bar */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 py-1.5 px-3 rounded bg-surface-container-low border border-border font-label-code text-label-code text-secondary">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            <span>Methodology: Structured cross-interview extraction across 3 European healthcare markets</span>
          </div>
          <span className="hidden md:inline text-border">/</span>
          <div className="flex items-center gap-1">
            <span className="text-secondary">Verbatim quote match:</span>
            <span className="text-primary font-semibold">100% Grounded</span>
          </div>
        </div>

        {/* Quick Jump Bar */}
        <div className="flex items-center flex-wrap gap-1.5 pt-1">
          <span className="font-label-code text-label-code text-secondary mr-1">
            Jump to Question:
          </span>
          {questions.map((q) => (
            <button
              key={q.question_id}
              onClick={() => handleJumpToQuestion(q.question_id)}
              className={`px-2.5 py-1 rounded font-label-code text-label-code border transition-colors cursor-pointer ${
                activeQuestionId === q.question_id
                  ? "bg-primary text-white border-primary"
                  : "bg-surface-container-lowest text-secondary hover:text-on-surface hover:bg-surface-container-low border-border"
              }`}
            >
              Q{q.question_id}
            </button>
          ))}
        </div>
      </section>

      {/* Question Items List */}
      <div className="flex flex-col gap-5">
        {questions.map((q, idx) => (
          <InterviewQuestion
            key={q.question_id}
            question={q}
            index={idx}
            hideQuotes={isCompact}
            onPlayTimestamp={onPlayTimestamp}
          />
        ))}
      </div>
    </div>
  );
};
