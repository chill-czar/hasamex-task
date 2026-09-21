"use client";

import React from "react";
import { LayoutDashboard, BookOpen, Lightbulb, MessageSquareQuote, FileText, Database } from "lucide-react";
import { HealthStatus } from "../lib/api";

export type NavTab = "overview" | "guide" | "insights" | "ask" | "evidence";

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthStatus | null;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab, health }) => {
  const tabs: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: "guide", label: "Interview Guide", icon: <BookOpen className="w-4 h-4" /> },
    { id: "insights", label: "Insights & Contrasts", icon: <Lightbulb className="w-4 h-4" /> },
    { id: "ask", label: "Ask Across Calls", icon: <MessageSquareQuote className="w-4 h-4" /> },
    { id: "evidence", label: "Evidence Explorer", icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-sm">
              H
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">HASAMEX</span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-medium border border-slate-700">
                  Research Analyst
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                European Robotic Surgery Market • Evidence-Grounded
              </p>
            </div>
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const active = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onSelectTab(tab.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                    active
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="hidden lg:flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>
                {health ? (
                  <span className="text-emerald-400 font-medium">Canonical DB Active</span>
                ) : (
                  <span className="text-amber-400 font-medium">Connecting...</span>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
