"use client";

import React, { useState } from "react";
import { Lightbulb, Split, Users, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { ThemeItem, DisagreementItem } from "../lib/api";
import { EvidenceCard } from "./EvidenceCard";

interface InsightsViewProps {
  themes: ThemeItem[];
  disagreements: DisagreementItem[];
  onNavigateToSegment: (segmentId: string, callId: string) => void;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  themes,
  disagreements,
  onNavigateToSegment,
}) => {
  const [activeTab, setActiveTab] = useState<"themes" | "disagreements">("themes");

  const getCategoryBadge = (category: string) => {
    switch (category.toLowerCase()) {
      case "contradiction":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-red-100 text-red-800 border border-red-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            Contradiction
          </span>
        );
      case "different emphasis":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <Info className="w-3.5 h-3.5" />
            Different Emphasis
          </span>
        );
      case "partial agreement":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Partial Agreement
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-200">
            {category}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* View Header and Tab Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            Cross-Interview Insights & Market Synthesis
          </h1>
          <p className="text-xs text-slate-500">
            Identify consensus themes and nuanced disagreements with exact grounded citations
          </p>
        </div>

        <div className="flex items-center p-1 bg-slate-100 rounded-lg border border-slate-200 w-fit">
          <button
            onClick={() => setActiveTab("themes")}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-all ${
              activeTab === "themes"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Lightbulb className="w-4 h-4 text-amber-500" />
            <span>Common Themes ({themes.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("disagreements")}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-all ${
              activeTab === "disagreements"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Split className="w-4 h-4 text-indigo-500" />
            <span>Contrasting Viewpoints ({disagreements.length})</span>
          </button>
        </div>
      </div>

      {/* Themes Tab */}
      {activeTab === "themes" && (
        <div className="grid grid-cols-1 gap-6">
          {themes.map((theme) => (
            <div
              key={theme.theme_id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0"></span>
                  {theme.title}
                </h2>
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium mr-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>Experts:</span>
                  </div>
                  {theme.markets.map((m, i) => (
                    <span
                      key={i}
                      className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>

              <p className="text-slate-700 text-sm leading-relaxed mb-5 bg-slate-50 p-3.5 rounded-lg border border-slate-100">
                {theme.summary}
              </p>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Multi-Call Supporting Quotes & Timestamps
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {theme.supporting_evidence.map((ev, evIdx) => (
                    <EvidenceCard
                      key={evIdx}
                      evidence={ev}
                      onNavigateToSegment={onNavigateToSegment}
                      compact={true}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Disagreements Tab */}
      {activeTab === "disagreements" && (
        <div className="grid grid-cols-1 gap-6">
          {disagreements.map((item) => (
            <div
              key={item.topic_id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
                <div>
                  <div className="flex items-center gap-2.5 mb-1.5">
                    {getCategoryBadge(item.category)}
                  </div>
                  <h2 className="text-base font-bold text-slate-900 leading-snug">
                    {item.topic}
                  </h2>
                </div>
              </div>

              <div className="bg-indigo-50/60 rounded-lg p-3.5 border border-indigo-100 my-4">
                <p className="text-xs text-indigo-900 font-medium leading-relaxed">
                  <span className="font-bold text-indigo-950 uppercase tracking-wide mr-1">
                    Analytical Synthesis:
                  </span>
                  {item.explanation}
                </p>
              </div>

              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Diverging Stances & Supporting Citations
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {item.stances.map((stance, sIdx) => (
                  <div
                    key={sIdx}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-sm text-slate-900">
                          {stance.expert_name}
                        </span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
                          {stance.market}
                        </span>
                      </div>

                      <p className="text-xs text-slate-700 font-medium leading-relaxed mb-2">
                        {stance.position}
                      </p>
                    </div>

                    <EvidenceCard
                      evidence={stance.evidence}
                      onNavigateToSegment={onNavigateToSegment}
                      compact={true}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
