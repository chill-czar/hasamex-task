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
} from "../lib/api";
import { Navbar, NavTab } from "../components/Navbar";
import { DashboardView } from "../components/DashboardView";
import { InterviewGuideView } from "../components/InterviewGuideView";
import { InsightsView } from "../components/InsightsView";
import { AskQuestionView } from "../components/AskQuestionView";
import { EvidenceExplorerView } from "../components/EvidenceExplorerView";
import { ShieldCheck, AlertCircle, Loader2 } from "lucide-react";

export default function Home() {
  const [currentTab, setCurrentTab] = useState<NavTab>("overview");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [interviews, setInterviews] = useState<CallSummary[]>([]);
  const [questions, setQuestions] = useState<GuideQuestionAnalysis[]>([]);
  const [themes, setThemes] = useState<ThemeItem[]>([]);
  const [disagreements, setDisagreements] = useState<DisagreementItem[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Deep-linking state for Evidence Explorer
  const [targetSegmentId, setTargetSegmentId] = useState<string | null>(null);
  const [targetCallId, setTargetCallId] = useState<string | null>(null);

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
      } catch (err: any) {
        console.error("Platform initialization error:", err);
        setError(err.message || "Failed to connect to Hasamex API service.");
      } finally {
        setLoading(false);
      }
    }
    loadPlatformData();
  }, []);

  const handleNavigateToSegment = (segmentId: string, callId: string) => {
    setTargetSegmentId(segmentId);
    setTargetCallId(callId);
    setCurrentTab("evidence");
  };

  const handleSelectExpertCall = (callId: string) => {
    setTargetCallId(callId);
    setTargetSegmentId(null);
    setCurrentTab("evidence");
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            <p className="text-sm text-slate-500 font-medium">
              Loading canonical interview dataset and verified analyses...
            </p>
          </div>
        ) : error ? (
          <div className="bg-white p-8 rounded-2xl border border-red-200 shadow-sm max-w-xl mx-auto text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">API Connection Required</h2>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Ensure the FastAPI backend is running at{" "}
                <code className="px-2 py-0.5 bg-slate-100 rounded text-indigo-600 font-mono">
                  http://localhost:8000
                </code>
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
            >
              Retry Connection
            </button>
          </div>
        ) : (
          <>
            {currentTab === "overview" && (
              <DashboardView
                interviews={interviews}
                health={health}
                onSelectTab={setCurrentTab}
                onSelectExpertCall={handleSelectExpertCall}
              />
            )}

            {currentTab === "guide" && (
              <InterviewGuideView
                questions={questions}
                onNavigateToSegment={handleNavigateToSegment}
              />
            )}

            {currentTab === "insights" && (
              <InsightsView
                themes={themes}
                disagreements={disagreements}
                onNavigateToSegment={handleNavigateToSegment}
              />
            )}

            {currentTab === "ask" && (
              <AskQuestionView onNavigateToSegment={handleNavigateToSegment} />
            )}

            {currentTab === "evidence" && (
              <EvidenceExplorerView
                interviews={interviews}
                targetSegmentId={targetSegmentId}
                targetCallId={targetCallId}
                onClearTarget={() => setTargetSegmentId(null)}
              />
            )}
          </>
        )}
      </main>

      {/* Trust & Architecture Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-slate-500 text-xs mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold text-slate-700">
              Evidence-First Invariant:
            </span>
            <span>
              Transcript evidence is authoritative. Quotes are verified verbatim and timestamps reflect canonical metadata.
            </span>
          </div>
          <div className="text-slate-400 text-[11px]">
            Hasamex Technical Case Study • Google GenAI + ADK + File Search + PostgreSQL
          </div>
        </div>
      </footer>
    </div>
  );
}
