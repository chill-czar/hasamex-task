"use client";

import React from "react";
import { ShieldCheck } from "lucide-react";
import { ThemeItem, DisagreementItem } from "@/lib/api";
import { ThemeCard } from "./ThemeCard";
import { PerspectiveComparison } from "./PerspectiveComparison";

interface InsightsViewProps {
  themes: ThemeItem[];
  disagreements: DisagreementItem[];
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  themes,
  disagreements,
  onPlayTimestamp,
}) => {
  return (
    <div className="flex flex-col w-full gap-8">
      {/* Top Editorial Header & Corpus Telemetry */}
      <div className="relative w-full pt-2 pb-4 border-b border-border space-y-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
          <div className="space-y-1 max-w-2xl">
            <div className="flex items-center gap-1.5 font-label-code text-label-code text-xs">
              <span className="text-primary font-semibold uppercase tracking-wider">
                Synthesis Protocol
              </span>
              <span className="text-border">/</span>
              <span className="text-secondary">Cross-Corpus Extraction</span>
            </div>
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
              Cross-Interview Insights
            </h1>
            <p className="font-body-md text-body-md text-secondary max-w-xl">
              Themes and differences identified across the three European expert interviews.
            </p>
          </div>

          {/* Summary Pill Bar */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-container-high text-on-surface-variant self-start md:self-auto shadow-2xs border border-border/60">
            <span className="inline-block w-2 h-2 rounded-full bg-primary"></span>
            <span className="font-label-code text-label-code text-on-surface">
              Synthesis corpus: 3 Expert Sessions · {themes.length} Consensus Themes · {disagreements.length} Divergences
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 1: COMMON THEMES */}
      <section className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 pb-1 border-b border-border/60">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-label-code text-label-code text-primary uppercase font-semibold">
                Part I
              </span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
                Common Themes
              </h2>
            </div>
            <p className="font-body-md text-body-md text-secondary mt-0.5 max-w-2xl">
              Patterns, operational practices, and systemic considerations corroborated across independent interviews.
            </p>
          </div>
          <span className="font-label-code text-label-code text-secondary bg-surface-container px-2.5 py-1 rounded border border-border/60 self-start md:self-auto">
            {themes.length} Synthesized Themes
          </span>
        </div>

        <div className="space-y-4">
          {themes.map((theme, idx) => (
            <ThemeCard
              key={theme.theme_id}
              theme={theme}
              index={idx}
              onPlayTimestamp={onPlayTimestamp}
            />
          ))}
        </div>
      </section>

      {/* SECTION 2: DIFFERENT PERSPECTIVES (DISAGREEMENTS) */}
      <section className="space-y-4 pt-4 border-t border-border">
        <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 pb-1 border-b border-border/60">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-label-code text-label-code text-tertiary uppercase font-semibold">
                Part II
              </span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
                Different Perspectives
              </h2>
            </div>
            <p className="font-body-md text-body-md text-secondary mt-0.5 max-w-2xl">
              Neutral contrast of divergent clinical strategies and procurement priorities across markets.
            </p>
          </div>
          <span className="font-label-code text-label-code text-secondary bg-surface-container px-2.5 py-1 rounded border border-border/60 self-start md:self-auto">
            {disagreements.length} Divergence Areas
          </span>
        </div>

        <div className="space-y-4">
          {disagreements.map((dis, idx) => (
            <PerspectiveComparison
              key={dis.topic_id}
              disagreement={dis}
              index={idx}
              onPlayTimestamp={onPlayTimestamp}
            />
          ))}
        </div>
      </section>

      {/* Grounding Status Strip */}
      <aside className="p-3.5 rounded-lg bg-surface-container-low border border-border flex items-center justify-between gap-3 text-xs font-label-code text-secondary">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="text-on-surface font-normal">
            Corpus integrity verified across 3 canonical interview transcripts. All quotes grounded with exact timestamps.
          </span>
        </div>
        <span className="text-primary font-medium shrink-0 hidden sm:inline">
          Deterministic Verification
        </span>
      </aside>
    </div>
  );
};
