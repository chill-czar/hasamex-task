"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Clock, User, Filter, FileText, CheckCircle, MapPin } from "lucide-react";
import { CallSummary, CallDetail, fetchInterviewDetail } from "../lib/api";

interface EvidenceExplorerViewProps {
  interviews: CallSummary[];
  targetSegmentId: string | null;
  targetCallId: string | null;
  onClearTarget: () => void;
}

export const EvidenceExplorerView: React.FC<EvidenceExplorerViewProps> = ({
  interviews,
  targetSegmentId,
  targetCallId,
  onClearTarget,
}) => {
  const [selectedCallId, setSelectedCallId] = useState<string>(
    targetCallId || (interviews[0]?.call_id ?? "call_fr_01")
  );
  const [callDetail, setCallDetail] = useState<CallDetail | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const segmentRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (targetCallId) {
      setSelectedCallId(targetCallId);
    }
  }, [targetCallId]);

  useEffect(() => {
    async function loadCall() {
      if (!selectedCallId) return;
      setLoading(true);
      setError(null);
      try {
        const detail = await fetchInterviewDetail(selectedCallId);
        setCallDetail(detail);
      } catch (err: any) {
        setError(err.message || "Failed to load transcript");
      } finally {
        setLoading(false);
      }
    }
    loadCall();
  }, [selectedCallId]);

  useEffect(() => {
    if (targetSegmentId && callDetail) {
      const el = segmentRefs.current[targetSegmentId];
      if (el) {
        setTimeout(() => {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 150);
      }
    }
  }, [targetSegmentId, callDetail]);

  const filteredSegments = (callDetail?.segments || []).filter((seg) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      seg.text.toLowerCase().includes(q) ||
      seg.speaker.toLowerCase().includes(q) ||
      seg.start_timestamp.includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header and Call Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            Canonical Evidence Explorer
          </h1>
          <p className="text-xs text-slate-500">
            Inspect authoritative verbatim transcripts with timestamps in seconds
          </p>
        </div>

        {/* Call Selector Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {interviews.map((call) => (
            <button
              key={call.call_id}
              onClick={() => {
                setSelectedCallId(call.call_id);
                onClearTarget();
              }}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                selectedCallId === call.call_id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{call.expert_name}</span>
              <span className="opacity-80 font-normal">({call.market})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Transcript Metadata Header */}
      {callDetail && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold">
              {callDetail.market === "France" ? "FR" : callDetail.market === "Germany" ? "DE" : "UK"}
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">{callDetail.title}</h2>
              <p className="text-xs text-slate-500">
                Source: <span className="font-mono">{callDetail.source_file}</span> • Duration:{" "}
                {Math.round(callDetail.total_duration_seconds / 60)} min • Total Turns:{" "}
                {callDetail.segments.length}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-64">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search within this transcript..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>
        </div>
      )}

      {/* Target Segment Notification Banner */}
      {targetSegmentId && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-indigo-600" />
            <span>
              Navigated from cited quote: Showing segment{" "}
              <span className="font-mono font-bold">{targetSegmentId}</span>
            </span>
          </div>
          <button
            onClick={onClearTarget}
            className="text-indigo-700 font-semibold hover:underline"
          >
            Dismiss highlight
          </button>
        </div>
      )}

      {/* Transcript Segments List */}
      <div className="space-y-3">
        {filteredSegments.map((seg) => {
          const isTarget = targetSegmentId === seg.segment_id;

          return (
            <div
              key={seg.segment_id}
              ref={(el) => {
                segmentRefs.current[seg.segment_id] = el;
              }}
              className={`p-4 rounded-xl border transition-all ${
                isTarget
                  ? "bg-indigo-50/80 border-indigo-400 ring-2 ring-indigo-400/30 shadow-md"
                  : seg.is_expert
                  ? "bg-white border-slate-200 shadow-2xs hover:border-slate-300"
                  : "bg-slate-50/60 border-slate-200/80 text-slate-600"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <User className={`w-3.5 h-3.5 ${seg.is_expert ? "text-indigo-600" : "text-slate-400"}`} />
                  <span
                    className={`text-xs font-bold ${
                      seg.is_expert ? "text-slate-900" : "text-slate-600"
                    }`}
                  >
                    {seg.speaker}
                  </span>
                  {seg.is_expert && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                      Expert Answer
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="inline-flex items-center gap-1 font-mono text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {seg.start_timestamp} – {seg.end_timestamp} ({seg.start_time_seconds.toFixed(0)}s)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {seg.segment_id}
                  </span>
                </div>
              </div>

              <p
                className={`text-sm leading-relaxed ${
                  seg.is_expert ? "text-slate-800" : "text-slate-600 italic"
                }`}
              >
                {seg.text}
              </p>
            </div>
          );
        })}

        {filteredSegments.length === 0 && (
          <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
            No segments matching "{searchQuery}" found in this transcript.
          </div>
        )}
      </div>
    </div>
  );
};
