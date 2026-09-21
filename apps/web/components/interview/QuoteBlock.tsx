"use client";

import React from "react";

interface QuoteBlockProps {
  quote: string;
  variant?: "primary" | "tertiary" | "secondary";
  className?: string;
  hidden?: boolean;
}

export const QuoteBlock: React.FC<QuoteBlockProps> = ({
  quote,
  variant = "primary",
  className = "",
  hidden = false,
}) => {
  if (hidden) return null;

  const borderColor =
    variant === "tertiary"
      ? "border-tertiary"
      : variant === "secondary"
      ? "border-secondary"
      : "border-primary";

  return (
    <blockquote
      className={`border-l-[3px] ${borderColor} pl-4 py-1.5 italic font-body-lg-quote text-body-lg-quote text-zinc-900 bg-surface-container-low/70 rounded-r transition-all ${className}`}
    >
      &ldquo;{quote.replace(/^["“]|["”]$/g, "")}&rdquo;
    </blockquote>
  );
};
