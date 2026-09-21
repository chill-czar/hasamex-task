"use client";

import React, { useState } from "react";
import { Navigation, NavTab } from "./Navigation";
import { AudioPlaybackDrawer, AudioPlaybackState } from "./AudioPlaybackDrawer";
import { CallSummary, HealthStatus } from "@/lib/api";

interface AppShellProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  interviews: CallSummary[];
  health: HealthStatus | null;
  children: (helpers: {
    playTimestamp: (item: {
      speaker: string;
      interview: string;
      timestamp: string;
      quote: string;
    }) => void;
  }) => React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  interviews,
  health,
  children,
}) => {
  const [playback, setPlayback] = useState<AudioPlaybackState>({
    isOpen: false,
    speaker: "",
    interview: "",
    timestamp: "",
    quote: "",
  });

  const handlePlayTimestamp = (item: {
    speaker: string;
    interview: string;
    timestamp: string;
    quote: string;
  }) => {
    setPlayback({
      isOpen: true,
      speaker: item.speaker,
      interview: item.interview,
      timestamp: item.timestamp,
      quote: item.quote,
    });
  };

  const handleClosePlayback = () => {
    setPlayback((prev) => ({ ...prev, isOpen: false }));
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface text-on-surface antialiased">
      {/* Top Header */}
      <Navigation
        currentTab={currentTab}
        onSelectTab={onSelectTab}
        interviews={interviews}
        health={health}
      />

      {/* Main Container constrained to max-w-5xl matching Stitch */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 lg:px-0 pt-20 pb-16">
        {children({ playTimestamp: handlePlayTimestamp })}
      </main>

      {/* Audio Playback Drawer */}
      <AudioPlaybackDrawer
        playback={playback}
        onClose={handleClosePlayback}
      />

      {/* Archival Diligence Footer matching Stitch */}
      <footer className="w-full border-t border-border bg-surface-container-lowest py-6">
        <div className="max-w-5xl mx-auto px-4 lg:px-0 flex flex-col sm:flex-row items-center justify-between gap-2 font-label-code text-label-code text-secondary text-xs">
          <span>Technical Case Study Demo · Diligence Workbench</span>
          <span>Deterministic Transcript Analysis Platform</span>
        </div>
      </footer>
    </div>
  );
};
