"use client";

import React, { useEffect } from "react";
import { Volume2, X } from "lucide-react";

export interface AudioPlaybackState {
  isOpen: boolean;
  speaker: string;
  interview: string;
  timestamp: string;
  quote: string;
}

interface AudioPlaybackDrawerProps {
  playback: AudioPlaybackState;
  onClose: () => void;
}

export const AudioPlaybackDrawer: React.FC<AudioPlaybackDrawerProps> = ({
  playback,
  onClose,
}) => {
  useEffect(() => {
    if (!playback.isOpen) return;

    // Auto-dismiss after 8 seconds of inactivity
    const timer = setTimeout(() => {
      onClose();
    }, 8000);

    return () => clearTimeout(timer);
  }, [playback.isOpen, playback.timestamp, onClose]);

  if (!playback.isOpen) return null;

  return (
    <aside
      className="fixed bottom-4 right-4 max-w-md w-[calc(100vw-2rem)] sm:w-full bg-surface-container-lowest border border-border rounded-xl shadow-xl p-4 transition-all duration-300 z-50 animate-in slide-in-from-bottom-5 fade-in"
      role="region"
      aria-label="Audio Anchor Playback Drawer"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
            <Volume2 className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-label-code text-label-code font-semibold text-on-surface">
                {playback.interview || "Canonical Audio"}
              </span>
              <span className="text-border">·</span>
              <span className="font-label-code text-label-code text-primary font-bold">
                [ {playback.timestamp} ]
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-secondary">
              {playback.speaker}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="text-secondary hover:text-on-surface p-1 rounded hover:bg-surface-container transition-colors cursor-pointer"
          aria-label="Close audio preview"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Mini Progress Waveform Mock */}
      <div className="mt-3 pt-2 border-t border-border/60 flex flex-col gap-1.5">
        <div className="flex items-center justify-between font-label-code text-[10px] text-secondary">
          <span>{playback.timestamp}</span>
          <span className="flex items-center gap-1 text-emerald-700 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            <span>Synchronized Audio Anchor</span>
          </span>
          <span>Verified Track</span>
        </div>

        <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden flex items-center">
          <div className="bg-primary h-full w-2/5 animate-pulse"></div>
        </div>

        {playback.quote && (
          <p className="font-body-sm text-body-sm text-on-surface italic line-clamp-2 mt-1">
            &ldquo;{playback.quote}&rdquo;
          </p>
        )}
      </div>
    </aside>
  );
};
