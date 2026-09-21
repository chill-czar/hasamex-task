"use client";

import React from "react";
import { Users, FileText, HelpCircle, ArrowRight, Activity, MapPin, Building2, ShieldCheck, Cpu } from "lucide-react";
import { CallSummary, HealthStatus } from "../lib/api";
import { NavTab } from "./Navbar";

interface DashboardViewProps {
  interviews: CallSummary[];
  health: HealthStatus | null;
  onSelectTab: (tab: NavTab) => void;
  onSelectExpertCall: (callId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  interviews,
  health,
  onSelectTab,
  onSelectExpertCall,
}) => {
  const totalSegments = interviews.reduce((acc, c) => acc + c.segment_count, 0);

  const expertDetails: Record<string, { specialty: string; hospitalTier: string; keyFocus: string }> = {
    expert_fr_martin: {
      specialty: "Surgical Urology",
      hospitalTier: "Academic Medical Centres & Private Clinics",
      keyFocus: "Capital budget committees, multi-surgeon utilization, 15-20% steady growth.",
    },
    expert_de_keller: {
      specialty: "Hospital Procurement & Finance",
      hospitalTier: "University Hospitals vs. Community Facilities",
      keyFocus: "Total Cost of Ownership (TCO), service contracts, conservative high-single/low-double digit growth.",
    },
    expert_gb_carter: {
      specialty: "NHS Consultant Urology",
      hospitalTier: "Major NHS Trusts & Teaching Hospitals",
      keyFocus: "Workforce training capacity, clinical strategy balance, length of stay, >15% potential growth.",
    },
  };

  return (
    <div className="space-y-8">
      {/* Hero / Executive Brief */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg border border-slate-800">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-medium border border-indigo-500/30 mb-4">
            <ShieldCheck className="w-3.5 h-3.5" />
            Evidence-First Expert Intelligence
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-3">
            European Robotic Surgery Market Study
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Synthesized expert interview analysis covering hospital adoption, capital purchasing barriers,
            ROI models, and operational training constraints across France, Germany, and the United Kingdom.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => onSelectTab("guide")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors shadow-sm"
            >
              <span>Explore Interview Guide</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onSelectTab("insights")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition-colors"
            >
              <span>View Themes & Disagreements</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Interviews</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{interviews.length || 3}</div>
          <p className="text-xs text-slate-500 mt-1">Transcripts (FR, DE, UK)</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Experts</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{interviews.length || 3}</div>
          <p className="text-xs text-slate-500 mt-1">Urology & Procurement Leaders</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Segments</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalSegments || 25}</div>
          <p className="text-xs text-slate-500 mt-1">Canonical timestamped turns</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Guide Questions</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <HelpCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">6</div>
          <p className="text-xs text-slate-500 mt-1">Pre-analyzed core questions</p>
        </div>
      </div>

      {/* Expert Breakdown Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Expert Panel Profiles</h2>
            <p className="text-xs text-slate-500">
              Primary interview sources analyzed in the European market study
            </p>
          </div>
          <button
            onClick={() => onSelectTab("evidence")}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>View All Transcripts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {interviews.map((call) => {
            const meta = expertDetails[call.expert_id] || {
              specialty: "Clinical Leadership",
              hospitalTier: "Regional / Academic",
              keyFocus: "Market economics and surgical adoption.",
            };

            return (
              <div
                key={call.call_id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:border-indigo-300 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{call.expert_name}</h3>
                      <p className="text-xs font-medium text-indigo-600 mt-0.5">{call.expert_role}</p>
                    </div>
                    <span className="px-2 py-1 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      {call.market}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs text-slate-600 my-4 pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-2">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{meta.hospitalTier}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <Cpu className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <span>{meta.keyFocus}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500">
                    {call.segment_count} dialogue turns ({Math.round(call.total_duration_seconds / 60)} min)
                  </span>
                  <button
                    onClick={() => {
                      onSelectExpertCall(call.call_id);
                      onSelectTab("evidence");
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    <span>Read Call</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Grounding & Verification Architecture Box */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-100 text-emerald-800 mt-0.5">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">
              Deterministic Verification Architecture
            </h4>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              Every quote and insight across this platform is resolved against the authoritative
              canonical database in PostgreSQL. The LLM is never treated as the source of truth—quotes are
              verified verbatim and timestamps are anchored to source segment metadata in seconds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
