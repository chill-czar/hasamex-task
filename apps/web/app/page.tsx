"use client";

import React, { useState, useEffect } from "react";
import {
  fetchHealth,
  fetchInterviews,
  fetchGuideQuestions,
  fetchThemes,
  fetchDisagreements,
  HealthStatus,
  CallSummary,
  GuideQuestionAnalysis,
  ThemeItem,
  DisagreementItem,
} from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { NavTab } from "@/components/layout/Navigation";
import { InterviewGuideView } from "@/components/interview/InterviewGuideView";
import { InsightsView } from "@/components/insights/InsightsView";
import { AskQuestionView } from "@/components/ask/AskQuestionView";
import { AlertCircle, Loader2 } from "lucide-react";

export default function Home() {
  const [currentTab, setCurrentTab] = useState<NavTab>("guide");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [interviews, setInterviews] = useState<CallSummary[]>([]);
  const [questions, setQuestions] = useState<GuideQuestionAnalysis[]>([]);
  const [themes, setThemes] = useState<ThemeItem[]>([]);
  const [disagreements, setDisagreements] = useState<DisagreementItem[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPlatformData() {
      try {
        setLoading(true);
        const [h, invs, qs, ths, dis] = await Promise.all([
          fetchHealth(),
          fetchInterviews(),
          fetchGuideQuestions(),
          fetchThemes(),
          fetchDisagreements(),
        ]);
        setHealth(h);
        setInterviews(invs);
        setQuestions(qs);
        setThemes(ths);
        setDisagreements(dis);
      } catch (err: unknown) {
        console.error("Platform initialization error:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to connect to Interview Analyst API service."
        );
      } finally {
        setLoading(false);
      }
    }
    loadPlatformData();
  }, []);

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      interviews={interviews}
      health={health}
    >
      {({ playTimestamp }) => (
        <>
          {loading ? (
            <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm font-label-code text-secondary">
                Loading canonical interview dataset and verified analyses...
              </p>
            </div>
          ) : error ? (
            <div className="bg-surface-container-lowest p-8 rounded-xl border border-destructive/30 shadow-xs max-w-xl mx-auto text-center space-y-4 my-12">
              <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-headline-sm text-on-surface">
                  API Connection Required
                </h2>
                <p className="text-xs text-secondary mt-1 leading-relaxed">
                  Ensure the FastAPI backend is running at{" "}
                  <code className="px-2 py-0.5 bg-surface-container-high rounded text-primary font-label-code">
                    http://localhost:8000
                  </code>
                </p>
              </div>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-primary hover:bg-primary-container text-white rounded-lg text-xs font-semibold cursor-pointer shadow-xs"
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <>
              {currentTab === "guide" && (
                <InterviewGuideView
                  questions={questions}
                  onPlayTimestamp={playTimestamp}
                />
              )}

              {currentTab === "insights" && (
                <InsightsView
                  themes={themes}
                  disagreements={disagreements}
                  onPlayTimestamp={playTimestamp}
                />
              )}

              {currentTab === "ask" && (
                <AskQuestionView onPlayTimestamp={playTimestamp} />
              )}
            </>
          )}
        </>
      )}
    </AppShell>
  );
}
