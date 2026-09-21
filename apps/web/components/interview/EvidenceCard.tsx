"use client";

import React from "react";
import { CheckCircle2 } from "lucide-react";
import { EvidenceItem } from "@/lib/api";
import { TimestampButton } from "./TimestampButton";
import { QuoteBlock } from "./QuoteBlock";

interface EvidenceCardProps {
  evidence: EvidenceItem;
  label?: string;
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
  hideQuote?: boolean;
  compact?: boolean;
  variant?: "primary" | "tertiary" | "secondary";
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  label,
  onPlayTimestamp,
  hideQuote = false,
  compact = false,
  variant = "primary",
}) => {
  const speakerName = evidence.expert_name || evidence.speaker;
  const interviewInfo = evidence.market
    ? `${evidence.market} · ${evidence.speaker || "Expert"}`
    : evidence.call_id;

  const handlePlay = () => {
    onPlayTimestamp?.({
      speaker: speakerName,
      interview: interviewInfo,
      timestamp: evidence.start_timestamp,
      quote: evidence.quote,
    });
  };

  if (compact) {
    return (
      <div className="flex flex-col gap-1.5 py-1">
        <div className="flex flex-wrap items-center justify-between gap-1">
          <div className="flex items-center gap-1.5 font-label-code text-label-code text-on-surface">
            <span className="font-semibold text-primary">{speakerName}</span>
            <span className="text-secondary text-xs">
              · {evidence.market ? `${evidence.market}` : ""} ({evidence.speaker})
            </span>
          </div>
          <TimestampButton
            timestamp={evidence.start_timestamp}
            onClick={handlePlay}
          />
        </div>
        {!hideQuote && (
          <QuoteBlock quote={evidence.quote} variant={variant} />
        )}
      </div>
    );
  }

  return (
    <article className="p-4 bg-surface-container-lowest rounded-xl border border-border shadow-xs hover:shadow-sm transition-all flex flex-col justify-between gap-3">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div>
            {label && (
              <span className="font-label-sm text-label-sm text-primary uppercase font-bold tracking-wider block">
                {label}
              </span>
            )}
            <div className="font-headline-sm text-[15px] leading-snug text-on-surface font-semibold mt-0.5">
              {speakerName}
            </div>
            <div className="font-label-code text-label-code text-secondary">
              {evidence.market} · {evidence.speaker}
            </div>
          </div>
          <TimestampButton
            timestamp={evidence.start_timestamp}
            onClick={handlePlay}
          />
        </div>

        {!hideQuote && (
          <QuoteBlock quote={evidence.quote} variant={variant} className="mt-1" />
        )}
      </div>

      <div className="flex items-center justify-between text-secondary font-label-code text-label-code pt-2 border-t border-border/80">
        <span className="flex items-center gap-1 text-emerald-700">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Verified verbatim quote</span>
        </span>
        {evidence.relevance && (
          <span className="text-[11px] text-secondary truncate max-w-[200px]" title={evidence.relevance}>
            {evidence.relevance}
          </span>
        )}
      </div>
    </article>
  );
};
