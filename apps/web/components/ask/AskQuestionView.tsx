"use client";

import React, { useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";
import { QueryAnswer, askQuestion, askQuestionStream } from "@/lib/api";
import { QuestionInput } from "./QuestionInput";
import { AnswerResult } from "./AnswerResult";

interface AskQuestionViewProps {
  onPlayTimestamp?: (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => void;
}

export const AskQuestionView: React.FC<AskQuestionViewProps> = ({
  onPlayTimestamp,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [result, setResult] = useState<QueryAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async (query: string, marketFilter?: string) => {
    setIsLoading(true);
    setIsStreaming(true);
    setError(null);
    setResult(null);

    let accumulated = "";

    try {
      await askQuestionStream(query, marketFilter, {
        onToken: (token) => {
          accumulated += token;
          setResult((prev) => ({
            query,
            answer: accumulated,
            has_sufficient_evidence: true,
            evidence: prev?.evidence || [],
            themes_detected: prev?.themes_detected || ["Live Grounded Retrieval"],
            markets_covered: prev?.markets_covered || ["Europe"],
          }));
          setIsLoading(false);
        },
        onEvidence: (payload) => {
          setResult((prev) => ({
            query,
            answer: prev?.answer || accumulated,
            has_sufficient_evidence: payload.has_sufficient_evidence,
            evidence: payload.evidence,
            themes_detected: payload.themes_detected,
            markets_covered: payload.markets_covered,
          }));
        },
        onDone: () => {
          setIsStreaming(false);
          setIsLoading(false);
        },
        onError: (err) => {
          setError(err.message);
          setIsStreaming(false);
          setIsLoading(false);
        },
      });
    } catch {
      // Graceful fallback to standard request
      try {
        const res = await askQuestion(query, marketFilter);
        setResult(res);
      } catch (fallbackErr: unknown) {
        setError(fallbackErr instanceof Error ? fallbackErr.message : "Failed to execute query across transcripts.");
      } finally {
        setIsStreaming(false);
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="flex flex-col w-full gap-6">
      {/* Header Section */}
      <section className="w-full pt-2 pb-4 border-b border-border space-y-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
          <div className="max-w-2xl space-y-1">
            <div className="inline-flex items-center gap-1.5 font-label-code text-label-code text-xs text-primary uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span>Cross-Corpus Synthesis Engine</span>
            </div>
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
              Ask Across Interviews
            </h1>
            <p className="font-body-md text-body-md text-secondary">
              Query the primary corpus directly. All synthetic insights are strictly bound by verified line-level citations.
            </p>
          </div>

          {/* Corpus Metrics Pill Bar */}
          <div className="flex items-center gap-2 shrink-0 self-start md:self-auto font-label-code text-label-code text-xs">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container-low text-on-surface-variant border border-border/60">
              <span>3 Transcripts / France · Germany · UK</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container-low text-on-surface-variant border border-border/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
              <span>Deterministic Rigor: Strict</span>
            </div>
          </div>
        </div>

        {/* Query Input Component */}
        <QuestionInput onSubmit={handleQuery} isLoading={isLoading} />
      </section>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state skeleton */}
      {isLoading && !result && (
        <div className="py-12 flex flex-col items-center justify-center gap-3 text-secondary font-label-code text-sm">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <span>Synthesizing cross-interview evidence &amp; verifying exact citations...</span>
        </div>
      )}

      {/* Answer Presentation */}
      {result && (
        <div className="space-y-2">
          {isStreaming && (
            <div className="flex items-center gap-2 text-xs font-label-code text-primary animate-pulse">
              <span className="w-2 h-2 rounded-full bg-primary"></span>
              <span>Streaming live grounded synthesis...</span>
            </div>
          )}
          <AnswerResult result={result} onPlayTimestamp={onPlayTimestamp} />
        </div>
      )}
    </div>
  );
};
