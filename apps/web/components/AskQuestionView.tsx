"use client";

import React, { useState } from "react";
import { Search, Sparkles, AlertCircle, ShieldCheck, Send, CornerDownLeft, Loader2 } from "lucide-react";
import { QueryAnswer, askQuestion } from "../lib/api";
import { EvidenceCard } from "./EvidenceCard";

interface AskQuestionViewProps {
  onNavigateToSegment: (segmentId: string, callId: string) => void;
}

export const AskQuestionView: React.FC<AskQuestionViewProps> = ({ onNavigateToSegment }) => {
  const [query, setQuery] = useState("");
  const [marketFilter, setMarketFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<QueryAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleQuestions = [
    "What were the biggest challenges mentioned by the experts?",
    "Where did the experts disagree?",
    "Which expert emphasized cost and procurement?",
    "How important are surgeon training and clinical outcomes?",
    "What adoption trend is expected over the next 3 to 5 years?",
    "What is the typical purchasing decision timeline across Europe?",
    "What unique concern did Expert 2 raise regarding single-surgeon utilization?",
    "What is the adoption of robotic surgery in Japan?", // tests insufficient evidence safeguard
  ];

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim() || isLoading) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await askQuestion(searchQuery, marketFilter || undefined);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to execute query");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900">
          Ask Across Expert Interviews
        </h1>
        <p className="text-xs text-slate-500">
          Grounded cross-transcript retrieval with exact quote and timestamp validation
        </p>
      </div>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask an arbitrary question across all 3 transcripts..."
            className="w-full pl-11 pr-24 py-3.5 bg-white rounded-xl border border-slate-300 shadow-sm text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
          <Search className="w-5 h-5 text-slate-400 absolute left-3.5 pointer-events-none" />

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Ask</span>
                <CornerDownLeft className="w-3.5 h-3.5 opacity-80" />
              </>
            )}
          </button>
        </div>

        {/* Market Filter Chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-medium">Market Filter:</span>
          {[
            { id: "", label: "All Markets (FR, DE, UK)" },
            { id: "France", label: "🇫🇷 France" },
            { id: "Germany", label: "🇩🇪 Germany" },
            { id: "United Kingdom", label: "🇬🇧 UK" },
          ].map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMarketFilter(m.id)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                marketFilter === m.id
                  ? "bg-indigo-100 text-indigo-800 border border-indigo-200"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </form>

      {/* Suggested Questions */}
      <div>
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
          Suggested Research Questions:
        </span>
        <div className="flex flex-wrap gap-2">
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
                handleSearch(sq);
              }}
              className="text-xs text-slate-700 bg-white hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 border border-slate-200 px-3 py-1.5 rounded-lg transition-colors text-left"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Answer Presentation */}
      {result && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2 text-indigo-900 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Grounded Answer</span>
            </div>
            {result.has_sufficient_evidence ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5" />
                Verified Against Canonical Transcripts
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                <AlertCircle className="w-3.5 h-3.5" />
                Insufficient Evidence Guardrail Triggered
              </span>
            )}
          </div>

          <p className="text-slate-800 text-sm leading-relaxed whitespace-pre-line font-normal">
            {result.answer}
          </p>

          {/* Evidence Section */}
          {result.evidence.length > 0 && (
            <div className="pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Supporting Evidence ({result.evidence.length} verified quotes)
                </h3>
                <span className="text-[11px] text-slate-400">
                  Click any timestamp to view in original transcript
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.evidence.map((ev, i) => (
                  <EvidenceCard
                    key={i}
                    evidence={ev}
                    onNavigateToSegment={onNavigateToSegment}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
