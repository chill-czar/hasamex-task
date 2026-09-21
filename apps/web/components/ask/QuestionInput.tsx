"use client";

import React, { useState } from "react";
import { Search, Zap, Loader2 } from "lucide-react";

interface QuestionInputProps {
  onSubmit: (query: string, marketFilter?: string) => void;
  isLoading: boolean;
  initialQuery?: string;
}

export const QuestionInput: React.FC<QuestionInputProps> = ({
  onSubmit,
  isLoading,
  initialQuery = "",
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [marketFilter, setMarketFilter] = useState<string>("");

  const sampleQueries = [
    "What were the biggest challenges mentioned by the experts?",
    "Where did the experts disagree?",
    "Which expert emphasized cost and procurement?",
    "How important are surgeon training and clinical outcomes?",
    "What adoption trend is expected over the next 3 to 5 years?",
    "What is the typical purchasing decision timeline across Europe?",
    "What unique concern was raised regarding single-surgeon utilization?",
    "What is the adoption of robotic surgery in Japan?",
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmit(query.trim(), marketFilter || undefined);
  };

  const handleSelectSample = (sample: string) => {
    setQuery(sample);
    onSubmit(sample, marketFilter || undefined);
  };

  return (
    <div className="w-full space-y-3">
      {/* Search Input Bar matching Stitch */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-center w-full bg-surface-container-lowest rounded-xl border border-border shadow-xs transition-all focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20"
      >
        <div className="pl-4 pr-2 flex items-center pointer-events-none text-secondary">
          <Search className="w-5 h-5" />
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a technical, economic, or clinical question across interviews..."
          className="w-full py-3.5 pr-28 bg-transparent font-body-md text-body-md text-on-surface placeholder:text-secondary/60 focus:outline-none tracking-normal"
        />

        <div className="absolute right-2 flex items-center gap-2">
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary hover:bg-primary-container disabled:opacity-50 text-white font-body-sm text-body-sm font-medium transition-all shadow-xs cursor-pointer active:scale-[0.98]"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 fill-current" />
                <span>Ask</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Keyboard Shortcut Indicator & Market Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
        {/* Market Filter Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-label-code text-label-code text-secondary mr-1">
            Scope:
          </span>
          {[
            { id: "", label: "All Markets" },
            { id: "France", label: "🇫🇷 France" },
            { id: "Germany", label: "🇩🇪 Germany" },
            { id: "United Kingdom", label: "🇬🇧 UK" },
          ].map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMarketFilter(m.id)}
              className={`px-2 py-0.5 rounded font-label-code text-[11px] transition-colors cursor-pointer border ${
                marketFilter === m.id
                  ? "bg-primary text-white border-primary font-medium"
                  : "bg-surface-container-low text-secondary hover:text-on-surface hover:bg-surface-container border-border/60"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Enter Shortcut */}
        <div className="hidden sm:flex items-center gap-1.5 font-label-code text-label-code text-secondary text-[11px]">
          <span>Press</span>
          <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-[10px] border border-border">
            Enter ↵
          </kbd>
          <span>to execute query</span>
        </div>
      </div>

      {/* Suggested Sample Queries */}
      <div className="pt-2 border-t border-border/60 flex flex-wrap items-center gap-1.5">
        <span className="font-label-code text-label-code text-secondary mr-1 text-xs">
          Sample queries:
        </span>
        {sampleQueries.map((sq, i) => (
          <button
            key={i}
            type="button"
            onClick={() => handleSelectSample(sq)}
            className="px-2.5 py-1 rounded bg-surface-container-low hover:bg-surface-container hover:text-on-surface text-secondary font-body-sm text-body-sm text-xs transition-colors border border-border/50 cursor-pointer"
          >
            {sq}
          </button>
        ))}
      </div>
    </div>
  );
};
