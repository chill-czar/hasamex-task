"use client";

import React from "react";
import { Quote, Play } from "lucide-react";
import { ThemeItem, EvidenceItem } from "@/lib/api";
import { TimestampButton } from "@/components/interview/TimestampButton";

interface ThemeCardProps {
  theme: ThemeItem;
  index: number;
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const ThemeCard: React.FC<ThemeCardProps> = ({
  theme,
  index,
  onPlayTimestamp,
}) => {
  const formattedIndex = String(index + 1).padStart(2, "0");
  const primaryEvidence: EvidenceItem | undefined = theme.supporting_evidence[0];

  const handlePlayPrimary = () => {
    if (primaryEvidence) {
      onPlayTimestamp?.({
        speaker: primaryEvidence.expert_name || primaryEvidence.speaker,
        interview: primaryEvidence.market,
        timestamp: primaryEvidence.start_timestamp,
        quote: primaryEvidence.quote,
      });
    }
  };

  return (
    <article className="p-5 lg:p-6 rounded-xl bg-surface-container-lowest border border-border shadow-xs hover:shadow-sm transition-all">
      <div className="flex flex-col lg:flex-row gap-5">
        {/* Main Content Area */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-2">
            <span className="font-label-code text-label-code px-2 py-0.5 rounded bg-primary-fixed text-on-primary-fixed font-semibold">
              {formattedIndex}
            </span>
            <h3 className="font-headline-sm text-headline-sm text-on-surface">
              {theme.title}
            </h3>
          </div>

          <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
            {theme.summary}
          </p>

          {/* Mentioned By Chips */}
          <div className="pt-1 flex items-center flex-wrap gap-1.5 text-xs">
            <span className="font-label-code text-label-code text-secondary mr-1">
              Mentioned by:
            </span>
            {theme.experts.map((exp, i) => (
              <span
                key={i}
                className="font-label-code text-label-code px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant border border-border/60"
              >
                {exp}
              </span>
            ))}
          </div>

          {/* Secondary Evidence Snippets if more than 1 citation */}
          {theme.supporting_evidence.length > 1 && (
            <div className="pt-2 border-t border-border/60 space-y-1.5">
              <span className="font-label-sm text-label-sm text-secondary uppercase tracking-wider block">
                Additional Corroborating Citations ({theme.supporting_evidence.length - 1}):
              </span>
              <div className="flex flex-col gap-1.5">
                {theme.supporting_evidence.slice(1).map((ev, evIdx) => (
                  <div
                    key={evIdx}
                    className="flex items-center justify-between gap-2 p-2 rounded bg-surface-container-low/50 text-xs font-label-code"
                  >
                    <span className="text-secondary truncate">
                      <strong className="text-on-surface">{ev.expert_name || ev.speaker}</strong>: &ldquo;{ev.quote.slice(0, 75)}...&rdquo;
                    </span>
                    <TimestampButton
                      timestamp={ev.start_timestamp}
                      speaker={ev.expert_name || ev.speaker}
                      interview={ev.market}
                      quote={ev.quote}
                      onClick={() =>
                        onPlayTimestamp?.({
                          speaker: ev.expert_name || ev.speaker,
                          interview: ev.market,
                          timestamp: ev.start_timestamp,
                          quote: ev.quote,
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Evidence Callout Block (Stitch Right-Hand Highlight) */}
        {primaryEvidence && (
          <div className="w-full lg:w-[400px] shrink-0 bg-surface-container-low p-4 rounded-lg flex flex-col justify-between gap-3 border border-border/80">
            <div className="space-y-2">
              <div className="flex items-center justify-between font-label-code text-label-code text-secondary">
                <span className="flex items-center gap-1.5 font-medium text-primary">
                  <Quote className="w-3.5 h-3.5 fill-current" />
                  <span>Primary Grounded Quote</span>
                </span>
                <span className="px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface">
                  [ {primaryEvidence.start_timestamp} ]
                </span>
              </div>

              <blockquote className="font-body-lg-quote text-body-lg-quote italic text-on-surface leading-relaxed">
                &ldquo;{primaryEvidence.quote}&rdquo;
              </blockquote>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border/60">
              <span className="font-label-code text-label-code text-on-surface-variant truncate max-w-[200px]">
                {primaryEvidence.expert_name || primaryEvidence.speaker} · {primaryEvidence.market}
              </span>
              <button
                type="button"
                onClick={handlePlayPrimary}
                className="font-label-code text-label-code text-primary hover:text-indigo-900 flex items-center gap-1 transition-colors cursor-pointer"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>Play Segment</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </article>
  );
};
