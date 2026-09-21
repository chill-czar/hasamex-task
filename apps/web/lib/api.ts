/**
 * API client for the Hasamex Expert Interview Analysis Platform backend.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : typeof window !== "undefined"
    ? ""
    : "http://localhost:8000";

export interface Expert {
  expert_id: string;
  name: string;
  role: string;
  market: string;
  country_code: string;
  bio?: string;
}

export interface TranscriptSegment {
  segment_id: string;
  call_id: string;
  expert_id: string;
  speaker: string;
  is_expert: boolean;
  start_time_seconds: number;
  end_time_seconds: number;
  start_timestamp: string;
  end_timestamp: string;
  text: string;
}

export interface CallSummary {
  call_id: string;
  expert_id: string;
  expert_name: string;
  expert_role: string;
  market: string;
  country_code: string;
  title: string;
  total_duration_seconds: number;
  segment_count: number;
  source_file: string;
}

export interface CallDetail {
  call_id: string;
  expert_id: string;
  title: string;
  market: string;
  source_file: string;
  total_duration_seconds: number;
  segments: TranscriptSegment[];
}

export interface EvidenceItem {
  segment_id: string;
  call_id: string;
  expert_id: string;
  expert_name: string;
  speaker: string;
  market: string;
  quote: string;
  start_timestamp: string;
  end_timestamp: string;
  start_time_seconds: number;
  end_time_seconds: number;
  relevance?: string;
  verified: boolean;
  validation_notes?: string;
}

export interface ExpertAnswer {
  expert_id: string;
  expert_name: string;
  market: string;
  role: string;
  has_evidence: boolean;
  perspective_summary: string;
  evidence: EvidenceItem[];
}

export interface GuideQuestionAnalysis {
  question_id: number;
  question: string;
  synthesized_answer: string;
  expert_answers: ExpertAnswer[];
  common_themes: string[];
  contrasting_viewpoints: string[];
}

export interface ThemeItem {
  theme_id: string;
  title: string;
  summary: string;
  markets: string[];
  experts: string[];
  supporting_evidence: EvidenceItem[];
}

export interface ExpertStance {
  expert_id: string;
  expert_name: string;
  market: string;
  position: string;
  evidence: EvidenceItem;
}

export interface DisagreementItem {
  topic_id: string;
  topic: string;
  category: string;
  explanation: string;
  stances: ExpertStance[];
}

export interface QueryAnswer {
  query: string;
  answer: string;
  has_sufficient_evidence: boolean;
  evidence: EvidenceItem[];
  themes_detected: string[];
  markets_covered: string[];
}

export interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  gemini_configured: boolean;
  file_search_available: boolean;
  canonical_calls_loaded: number;
  canonical_experts_loaded: number;
}

export async function fetchHealth(): Promise<HealthStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchInterviews(): Promise<CallSummary[]> {
  const res = await fetch(`${API_BASE}/api/interviews`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch interviews");
  return await res.json();
}

export async function fetchInterviewDetail(callId: string): Promise<CallDetail> {
  const res = await fetch(`${API_BASE}/api/interviews/${callId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch interview ${callId}`);
  return await res.json();
}

export async function fetchGuideQuestions(): Promise<GuideQuestionAnalysis[]> {
  const res = await fetch(`${API_BASE}/api/interview-guide`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch interview guide analyses");
  return await res.json();
}

export async function fetchThemes(): Promise<ThemeItem[]> {
  const res = await fetch(`${API_BASE}/api/insights/themes`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch themes");
  return await res.json();
}

export async function fetchDisagreements(): Promise<DisagreementItem[]> {
  const res = await fetch(`${API_BASE}/api/insights/disagreements`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch disagreements");
  return await res.json();
}

export async function askQuestion(query: string, marketFilter?: string): Promise<QueryAnswer> {
  const res = await fetch(`${API_BASE}/api/questions/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, market_filter: marketFilter || null }),
  });
  if (!res.ok) throw new Error("Failed to process question");
  return await res.json();
}

export async function askQuestionStream(
  query: string,
  marketFilter?: string,
  callbacks?: {
    onToken?: (token: string) => void;
    onEvidence?: (evidencePayload: {
      evidence: EvidenceItem[];
      themes_detected: string[];
      markets_covered: string[];
      has_sufficient_evidence: boolean;
    }) => void;
    onDone?: () => void;
    onError?: (err: Error) => void;
  }
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/questions/ask-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, market_filter: marketFilter || null }),
  });

  if (!res.ok) {
    throw new Error(`Streaming request failed: ${res.statusText}`);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("ReadableStream not supported on response body.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const evtBlock of events) {
      if (!evtBlock.trim()) continue;
      let eventType = "message";
      let data = "";

      for (const line of evtBlock.split("\n")) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          data = line.slice(6);
        }
      }

      if (!data) continue;

      try {
        const parsed = JSON.parse(data);
        if (eventType === "token") {
          callbacks?.onToken?.(parsed.token);
        } else if (eventType === "evidence") {
          callbacks?.onEvidence?.(parsed);
        } else if (eventType === "done") {
          callbacks?.onDone?.();
        } else if (eventType === "error") {
          callbacks?.onError?.(new Error(parsed.error));
        }
      } catch {
        // Ignore parse errors on partial JSON
      }
    }
  }
}

export async function fetchEvidenceSegment(segmentId: string): Promise<TranscriptSegment> {
  const res = await fetch(`${API_BASE}/api/evidence/${segmentId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch evidence segment ${segmentId}`);
  return await res.json();
}
