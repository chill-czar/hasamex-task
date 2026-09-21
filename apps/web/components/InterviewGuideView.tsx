"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Sparkles, RefreshCw, Layers } from "lucide-react";
import { GuideQuestionAnalysis } from "../lib/api";
import { EvidenceCard } from "./EvidenceCard";

interface InterviewGuideViewProps {
  questions: GuideQuestionAnalysis[];
  onNavigateToSegment: (segmentId: string, callId: string) => void;
}

export const InterviewGuideView: React.FC<InterviewGuideViewProps> = ({
  questions,
  onNavigateToSegment,
}) => {
  const [selectedQuestionId, setSelectedQuestionId] = useState<number>(1);
  const [expandedCards, setExpandedCards] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: true,
    4: true,
    5: true,
    6: true,
  });

  const toggleCard = (id: number) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-xs font-semibold mb-1 border border-purple-200">
            <Layers className="w-3.5 h-3.5" />
            Interview Guide Analysis
          </div>
          <h1 className="text-xl font-bold text-slate-900">
            European Robotic Surgery Project Questions
          </h1>
          <p className="text-xs text-slate-500">
            Synthesized findings across France, Germany, and the UK with verified verbatim quotes
          </p>
        </div>

        {/* Quick jump tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {questions.map((q) => (
            <button
              key={q.question_id}
              onClick={() => {
                setSelectedQuestionId(q.question_id);
                setExpandedCards((prev) => ({ ...prev, [q.question_id]: true }));
                const el = document.getElementById(`question-${q.question_id}`);
                if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedQuestionId === q.question_id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              Q{q.question_id}
            </button>
          ))}
        </div>
      </div>

      {/* Question Accordion / Detail Cards */}
      <div className="space-y-6">
        {questions.map((q) => {
          const isExpanded = expandedCards[q.question_id] !== false;

          return (
            <div
              key={q.question_id}
              id={`question-${q.question_id}`}
              className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden transition-all"
            >
              {/* Header */}
              <div
                onClick={() => toggleCard(q.question_id)}
                className="p-5 cursor-pointer hover:bg-slate-50/70 transition-colors flex items-start justify-between gap-4 select-none"
              >
                <div className="flex items-start gap-3">
                  <span className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-800 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {q.question_id}
                  </span>
                  <div>
                    <h2 className="text-base font-bold text-slate-900 leading-snug">
                      {q.question}
                    </h2>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <span className="text-xs text-slate-500 font-medium">
                        3 Experts Quoted:
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-medium">
                        Dr. Martin (FR)
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-800 font-medium">
                        Anna Keller (DE)
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-medium">
                        Dr. Carter (UK)
                      </span>
                    </div>
                  </div>
                </div>

                <button className="text-slate-400 hover:text-slate-600 p-1">
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </button>
              </div>

              {isExpanded && (
                <div className="px-5 pb-6 pt-2 space-y-5 border-t border-slate-100 bg-slate-50/30">
                  {/* Synthesized Answer Box */}
                  <div className="bg-indigo-50/50 rounded-xl p-4 border border-indigo-100">
                    <div className="flex items-center gap-2 text-indigo-900 text-xs font-bold uppercase tracking-wider mb-2">
                      <Sparkles className="w-4 h-4 text-indigo-600" />
                      <span>Synthesized Cross-Market Answer</span>
                    </div>
                    <p className="text-slate-800 text-sm leading-relaxed font-normal">
                      {q.synthesized_answer}
                    </p>

                    {/* Common Themes & Contrasts */}
                    <div className="mt-3 pt-3 border-t border-indigo-100/80 flex flex-wrap gap-2 text-xs">
                      {q.common_themes.map((theme, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-md bg-white text-indigo-800 font-medium border border-indigo-200 shadow-2xs"
                        >
                          Consensus: {theme}
                        </span>
                      ))}
                      {q.contrasting_viewpoints.map((contrast, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 font-medium border border-amber-200 shadow-2xs"
                        >
                          Nuance: {contrast}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Side-by-Side Comparative Expert Perspectives */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                      Authoritative Expert Evidence & Exact Quotes
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {q.expert_answers.map((ea) => (
                        <div
                          key={ea.expert_id}
                          className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs flex flex-col justify-between space-y-3"
                        >
                          <div>
                            <div className="flex items-center justify-between gap-1 mb-2">
                              <div>
                                <h4 className="font-bold text-slate-900 text-sm">
                                  {ea.expert_name}
                                </h4>
                                <p className="text-[11px] text-slate-500">{ea.role}</p>
                              </div>
                              <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                                {ea.market}
                              </span>
                            </div>

                            <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100 leading-relaxed mb-3">
                              {ea.perspective_summary}
                            </p>
                          </div>

                          <div className="space-y-2">
                            {ea.evidence.map((ev, evIdx) => (
                              <EvidenceCard
                                key={evIdx}
                                evidence={ev}
                                onNavigateToSegment={onNavigateToSegment}
                                compact={true}
                              />
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
