"use client";

import React from "react";
import { ShieldCheck, Clock, ExternalLink, User } from "lucide-react";
import { EvidenceItem } from "../lib/api";

interface EvidenceCardProps {
  evidence: EvidenceItem;
  onNavigateToSegment?: (segmentId: string, callId: string) => void;
  compact?: boolean;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  onNavigateToSegment,
  compact = false,
}) => {
  const getMarketBadge = (market: string) => {
    const m = market.toLowerCase();
    if (m.includes("france")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          🇫🇷 France
        </span>
      );
    }
    if (m.includes("germany")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          🇩🇪 Germany
        </span>
      );
    }
    if (m.includes("united kingdom") || m.includes("uk")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          🇬🇧 United Kingdom
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
        {market}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-slate-500" />
          <span className="font-semibold text-slate-900 text-sm">
            {evidence.expert_name || evidence.speaker}
          </span>
          {getMarketBadge(evidence.market)}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateToSegment?.(evidence.segment_id, evidence.call_id)}
            title="Jump to exact transcript segment"
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-slate-100 text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 border border-slate-200 transition-colors"
          >
            <Clock className="w-3.5 h-3.5 text-indigo-600" />
            <span>{evidence.start_timestamp}</span>
            <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
          </button>

          {evidence.verified && (
            <span
              title="Verified verbatim match against canonical transcript record"
              className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Verified Quote
            </span>
          )}
        </div>
      </div>

      <div className="pl-3 border-l-2 border-indigo-400 my-2.5">
        <p className="text-slate-800 text-sm leading-relaxed italic font-serif">
          "{evidence.quote}"
        </p>
      </div>

      {evidence.relevance && !compact && (
        <p className="text-xs text-slate-500 mt-2">
          <span className="font-medium text-slate-600">Context:</span> {evidence.relevance}
        </p>
      )}
    </div>
  );
};
