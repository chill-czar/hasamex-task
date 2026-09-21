"use client";

import React from "react";
import { Scale } from "lucide-react";
import { DisagreementItem, ExpertStance } from "@/lib/api";
import { TimestampButton } from "@/components/interview/TimestampButton";

interface PerspectiveComparisonProps {
  disagreement: DisagreementItem;
  index: number;
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const PerspectiveComparison: React.FC<PerspectiveComparisonProps> = ({
  disagreement,
  index,
  onPlayTimestamp,
}) => {
  const formattedIndex = String(index + 1).padStart(2, "0");
  const [stanceA, stanceB] = disagreement.stances;

  const renderStanceColumn = (
    stance: ExpertStance | undefined,
    colorVariant: "primary" | "tertiary"
  ) => {
    if (!stance) return null;
    const isPrimary = colorVariant === "primary";
    const headerColor = isPrimary ? "text-primary" : "text-tertiary";
    const dotColor = isPrimary ? "bg-primary" : "bg-tertiary";

    return (
      <div className="bg-surface-container-low rounded-lg p-4 flex flex-col justify-between space-y-3 border border-border/70">
        <div className="space-y-2">
          <div className="flex items-center justify-between font-label-code text-label-code">
            <span className="text-secondary font-medium">
              {stance.expert_name} · {stance.market}
            </span>
            <TimestampButton
              timestamp={stance.evidence.start_timestamp}
              speaker={stance.expert_name}
              interview={stance.market}
              quote={stance.evidence.quote}
              onClick={() =>
                onPlayTimestamp?.({
                  speaker: stance.expert_name,
                  interview: stance.market,
                  timestamp: stance.evidence.start_timestamp,
                  quote: stance.evidence.quote,
                })
              }
            />
          </div>

          <h4 className={`font-headline-sm text-headline-sm ${headerColor} text-base leading-snug`}>
            {stance.position}
          </h4>

          <blockquote className="font-body-lg-quote text-body-lg-quote italic text-on-surface pt-1 leading-relaxed border-l-2 border-border/80 pl-3">
            &ldquo;{stance.evidence.quote}&rdquo;
          </blockquote>
        </div>

        <div className="pt-2 flex items-center gap-2 border-t border-border/50">
          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></span>
          <span className="font-label-code text-[11px] text-secondary">
            Verified Canonical Quote
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="rounded-xl bg-surface-container-lowest border border-border shadow-xs overflow-hidden p-5 lg:p-6 space-y-4">
      {/* Divergence Topic Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-label-code text-label-code px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-semibold">
            Divergence {formattedIndex}
          </span>
          <span className="font-label-code text-label-code text-secondary">
            Category: {disagreement.category}
          </span>
        </div>
        <h3 className="font-headline-sm text-headline-sm text-on-surface">
          {disagreement.topic}
        </h3>
      </div>

      {/* Comparative Two-Column Grid with Center Anchor */}
      <div className="relative grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        {renderStanceColumn(stanceA, "primary")}

        {/* Center floating VS indicator (Desktop) */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-surface-container-highest border border-border items-center justify-center font-label-code text-label-code text-on-surface-variant shadow-xs z-10 font-bold">
          vs.
        </div>

        {renderStanceColumn(stanceB, "tertiary")}
      </div>

      {/* Difference Analysis Box (Neutral Explanation) */}
      <div className="p-4 rounded-lg bg-surface-container-high/60 border border-border/80 space-y-1.5">
        <div className="flex items-center gap-1.5 font-label-code text-label-code text-on-surface font-semibold uppercase tracking-wider">
          <Scale className="w-3.5 h-3.5 text-primary" />
          <span>Difference Analysis</span>
        </div>
        <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
          {disagreement.explanation}
        </p>
      </div>
    </div>
  );
};
