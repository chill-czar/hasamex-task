"use client";

import React, { useState } from "react";
import { Play } from "lucide-react";

export interface TimestampButtonProps {
  timestamp: string;
  speaker?: string;
  interview?: string;
  quote?: string;
  onClick?: () => void;
  className?: string;
}

export const TimestampButton: React.FC<TimestampButtonProps> = ({
  timestamp,
  onClick,
  className = "",
}) => {
  const [clicked, setClicked] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setClicked(true);
    setTimeout(() => setClicked(false), 800);
    onClick?.();
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      title={`Play audio anchor at ${timestamp}`}
      className={`timestamp-trigger inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high hover:bg-primary hover:text-white border border-border font-label-code text-label-code text-secondary hover:text-white transition-all cursor-pointer select-none ${
        clicked ? "ring-2 ring-primary ring-offset-1 scale-[0.98]" : ""
      } ${className}`}
    >
      <Play className="w-2.5 h-2.5 fill-current" />
      <span>[ {timestamp} ]</span>
    </button>
  );
};
