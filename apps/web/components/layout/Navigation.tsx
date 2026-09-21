"use client";

import React, { useState } from "react";
import { Menu, X } from "lucide-react";
import { CallSummary, HealthStatus } from "@/lib/api";

export type NavTab = "guide" | "insights" | "ask";

interface NavigationProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  interviews: CallSummary[];
  health: HealthStatus | null;
}

export const Navigation: React.FC<NavigationProps> = ({
  currentTab,
  onSelectTab,
  interviews,
  health,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs: { id: NavTab; label: string }[] = [
    { id: "guide", label: "Interview Guide" },
    { id: "insights", label: "Insights" },
    { id: "ask", label: "Ask" },
  ];

  // Format short names of experts from database
  const rosterLabel = interviews.length > 0
    ? `${interviews.length} Interviews: ${interviews
        .map((inv) => inv.expert_name.split(" ").slice(-1)[0])
        .join(" · ")}`
    : "3 Interviews: Martin · Keller · Carter";

  const isHealthy = health?.status === "healthy";

  return (
    <header className="fixed top-0 w-full z-40 bg-surface-container-lowest/95 backdrop-blur-md border-b border-border">
      <div className="h-16 w-full max-w-5xl mx-auto px-4 lg:px-0 flex items-center justify-between gap-4">
        {/* Logo & Branding */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight font-semibold">
            Interview Analyst
          </span>
          <span className="hidden sm:inline font-label-code text-[11px] px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant uppercase tracking-wider border border-border">
            Expert Interview Analysis
          </span>
        </div>

        {/* Desktop Navigation Links matching Stitch */}
        <nav
          className="hidden md:flex items-center gap-6 lg:gap-8 h-full"
          aria-label="Main navigation"
        >
          {tabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onSelectTab(tab.id)}
                aria-current={active ? "page" : undefined}
                className={`inline-flex items-center h-full px-1 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
                  active
                    ? "text-on-surface border-primary font-semibold"
                    : "text-secondary hover:text-on-surface border-transparent"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Right Status Badges & Avatar */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <div className="hidden lg:flex items-center px-2.5 py-1 rounded bg-surface-container-low border border-border font-label-code text-[11px] text-secondary">
            <span className="truncate max-w-[220px]">{rosterLabel}</span>
          </div>

          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-lowest border border-border font-label-sm text-label-sm text-on-surface-variant"
            title={isHealthy ? "PostgreSQL & Gemini API Active" : "Connecting..."}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 ring-2 ring-emerald-100"></span>
            <span className="tracking-normal font-medium text-on-surface text-xs">
              {isHealthy ? "Analysis ready" : "Connecting..."}
            </span>
          </div>

          {/* User Icon indicator matching Stitch */}
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-label-code text-xs font-semibold">
            IA
          </div>

          {/* Mobile hamburger button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg text-secondary hover:text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-surface-container-lowest px-4 py-3 space-y-1 animate-in slide-in-from-top-2">
          {tabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  onSelectTab(tab.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  active
                    ? "bg-primary text-white"
                    : "text-secondary hover:bg-surface-container hover:text-on-surface"
                }`}
              >
                <span>{tab.label}</span>
                {active && <span className="w-1.5 h-1.5 rounded-full bg-white"></span>}
              </button>
            );
          })}

          <div className="pt-2 mt-2 border-t border-border flex items-center justify-between text-xs font-label-code text-secondary px-2">
            <span>Scope: {interviews.length} Interviews</span>
            <span className="text-emerald-700 font-medium">Grounding Verified</span>
          </div>
        </div>
      )}
    </header>
  );
};
