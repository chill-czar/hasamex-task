# Hasamex AI Engineer Case Study — Evidence-Grounded Expert Interview Analysis Platform Specification

## Problem Statement

Life sciences and healthcare strategy consulting firms (like Hasamex) conduct expert interview calls to understand market dynamics, such as the European robotic surgery market. Analysts currently spend hours manually combing through call transcripts from different countries, extracting quotes, reconciling timestamps, identifying common themes, and finding subtle disagreements between clinical and procurement stakeholders.

When AI/LLMs are applied naively to this process (e.g. standard chatbots or PDF question-answering tools):
1. Models hallucinate or subtly paraphrase quotes, violating citation integrity.
2. Models fabricate or drift on timestamps, making audio/video verification impossible.
3. Models fail to synthesize viewpoints across multiple national markets (France vs. Germany vs. UK) and diverse stakeholder roles (urologists vs. hospital procurement directors).
4. Models manufacture artificial disagreements where none exist or miss critical operational tensions (such as capital budget constraints vs. surgeon training bottlenecks).
5. At scale (30+ long transcripts), context windows blow up in latency, cost, and "lost-in-the-middle" attention failure.

The user needs a dedicated research workbench that treats **transcripts as the absolute source of truth** and guarantees that every insight, quote, and timestamp is deterministically grounded and verifiable.

---

## Solution

A production-grade, evidence-grounded research analysis platform built on:
- **FastAPI Backend + Google Gen AI SDK + Google ADK**: Provides structured intent routing and AI orchestration while strictly separating retrieval, reasoning, generation, and validation.
- **Managed Google File Search**: Indexes segment-level transcript documents for semantic retrieval with metadata filtering.
- **Canonical Transcript Store & Deterministic Validation Layer**: Authoritative PostgreSQL database (with SQLite local fallback) storing exact segment boundaries, speakers, and timestamps in seconds. An automated post-generation validation gate checks verbatim quote accuracy and overwrites timestamps with canonical metadata, rejecting hallucinations.
- **Next.js 15 App Router Frontend**: Enterprise research UI with dedicated views for:
  - **Executive Dashboard**: High-level dataset summary, expert profiles, market overview.
  - **Interview Guide View**: All 6 guide questions with cross-expert synthesized answers, comparative expert cards, exact quotes, and timestamp badges.
  - **Insights View**: Common market themes and categorized cross-call disagreements (agreements, partial agreements, different emphasis, contradictions).
  - **Ask Across Interviews**: Multi-transcript Q&A with grounded evidence cards and insufficient-evidence safeguards.
  - **Evidence Explorer**: Full interactive transcript viewer with search and clickable timestamp highlighting.
- **Automated Evaluation Suite**: Quantitative benchmarks measuring retrieval accuracy, citation accuracy, quote exactness, and groundedness.

---

## User Stories

### Ingestion & Canonical Storage
1. As a research analyst, I want raw transcripts to be ingested into canonical segments with deterministic IDs, speaker labels, and timestamps in seconds, so that all quotes are grounded in immutable source data.
2. As a platform engineer, I want the ingestion pipeline to index transcripts into Google File Search with metadata attributes (market, role, call ID), so that retrieval can be filtered without scanning full documents.
3. As a reviewer running the app locally, I want zero-friction database initialization with Docker Compose (PostgreSQL) and automatic SQLite fallback, so that the application runs immediately without complex environment setup.

### Interview Guide Analysis
4. As an analyst, I want to open the Interview Guide view and see the 6 standard questions from the European Robotic Surgery project pre-analyzed across France, Germany, and the UK.
5. As an analyst, I want each interview guide question to present a synthesized market summary followed by side-by-side expert perspectives (Dr. Jean Martin, Anna Keller, Dr. Emily Carter).
6. As an analyst, I want each expert's perspective to contain an exact verbatim quote and canonical timestamp, so that I can substantiate client deliverables.
7. As an analyst, I want questions where an expert gave no relevant input to explicitly state "Insufficient evidence in transcript" rather than fabricating an answer.

### Themes & Disagreements Analysis
8. As a strategy consultant, I want to view common themes across all three markets (e.g. capital budget barriers, training bottlenecks, utilization pressure), supported by quotes from multiple experts.
9. As a strategy consultant, I want to view contrasting viewpoints and disagreements classified along a spectrum (e.g. Agreement, Different Emphasis, Contradiction, Unique Viewpoint), so that nuance is preserved without manufacturing false hostility.
10. As a strategy consultant, I want to compare Dr. Martin's 15–20% adoption growth forecast against Anna Keller's conservative single/low-double-digit forecast and Dr. Carter's contingent >15% forecast with their exact supporting rationales.

### Cross-Transcript Q&A
11. As an analyst, I want to ask arbitrary free-form questions across all three transcripts (e.g. "What role does surgeon training play in hospital purchasing decisions?"), so that I can explore ad-hoc research hypotheses.
12. As an analyst, I want every Q&A answer to display a clear synthesis accompanied by expandable evidence cards showing the expert name, exact quote, and timestamp.
13. As an analyst, I want questions with no evidence in the transcripts (e.g. "What did the experts say about robotic surgery in Japan?") to return a clear "Insufficient evidence" notification rather than hallucinated speculation.

### Evidence Explorer & Auditability
14. As an analyst, I want an Evidence Explorer view where I can read the complete canonical transcripts of Dr. Jean Martin, Anna Keller, and Dr. Emily Carter.
15. As an analyst, I want clicking a timestamp or citation badge anywhere in the app to navigate to the Evidence Explorer and highlight the exact segment in the source transcript.
16. As an auditor, I want to see whether an evidence quote passed verbatim validation or was corrected against the canonical record.

### Scalability & Demo Presentation
17. As an interviewee presenting to Hasamex, I want a clear architecture diagram and demo script showing how the dual-engine design scales from 3 to 30+ long transcripts using Map-Reduce aggregation and top-k retrieval.
18. As a technical evaluator, I want an automated evaluation script (`python evaluation/evaluate.py`) that runs quantitative checks on retrieval, citation correctness, quote exactness, and groundedness.

---

## Implementation Decisions

### 1. Technology Stack
- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide React, shadcn/ui pattern.
- **Backend**: FastAPI, Python 3.12, Pydantic v2, `google-genai` (v2.24+), `google-adk` (v2.9+), `httpx`, `aiosqlite`, `asyncpg`/SQLAlchemy.
- **Retrieval**: Google File Search Store via `client.file_search_stores`.
- **Validation**: Deterministic sliding-window verbatim quote matcher and canonical timestamp resolver.
- **Containerization**: `docker-compose.yml` defining PostgreSQL and optional full-stack services.

### 2. Canonical Data Models
```python
class TranscriptSegment(BaseModel):
    segment_id: str          # e.g. seg_call_fr_01_002
    call_id: str             # e.g. call_fr_01
    expert_id: str           # e.g. expert_fr_martin
    speaker: str             # e.g. Dr. Martin
    start_time_seconds: float# e.g. 18.0
    end_time_seconds: float  # e.g. 72.0
    start_timestamp: str     # e.g. 00:18
    end_timestamp: str       # e.g. 01:12
    text: str                # exact verbatim transcript text
```

### 3. Agent & Intent Routing Architecture
- Root ADK Agent (`root_agent`) routes queries deterministically or via intent detection:
  - `INTERVIEW_GUIDE`: Fetches or computes analysis for the 6 guide questions.
  - `CROSS_CALL_ANALYSIS`: Dispatches comparative synthesis across all 3 experts.
  - `THEME_ANALYSIS`: Clusters consensus findings supported by multi-expert evidence.
  - `DISAGREEMENT_ANALYSIS`: Identifies diverging stances on growth, economics, and adoption.
  - `TRANSCRIPT_QA`: Retrieves top-k relevant segments and generates grounded answers.
  - `EVIDENCE_LOOKUP`: Direct canonical segment lookup by ID or query.

### 4. Post-Generation Evidence Validation Gate
- Every LLM-generated output containing evidence passes through `EvidenceValidator`:
  1. Verifies `call_id` and `expert_id` exist.
  2. Searches the canonical segments of that call for the cited quote.
  3. If found (verbatim or with minor punctuation/whitespace differences), snaps the quote to the exact canonical text and assigns the true canonical `start_timestamp` and `start_time_seconds`.
  4. If the quote cannot be verified in the canonical segments, the citation is marked unverified or discarded, ensuring no ungrounded claim reaches the UI.

### 5. API Contracts
- `GET /api/health` — Service health & configuration status
- `GET /api/interviews` — List of all 3 calls with expert metadata
- `GET /api/interviews/{call_id}` — Full canonical transcript and segments for a call
- `GET /api/interview-guide` — The 6 guide questions and pre-computed/cached synthesized answers
- `POST /api/interview-guide/analyze` — Trigger fresh analysis of a guide question
- `GET /api/insights/themes` — Common cross-call themes with supporting evidence
- `GET /api/insights/disagreements` — Cross-call contrasting viewpoints with evidence
- `POST /api/questions/ask` — Free-form Q&A with grounded evidence cards
- `GET /api/evidence/{segment_id}` — Direct segment retrieval for UI deep-linking

---

## Testing Decisions

### Seams for Testing
- **Highest Seam (System Workflow & API Seam)**: Testing endpoints via `httpx.AsyncClient` against the FastAPI application. Tests exercise parsing, canonical storage, retrieval, validation, and structured JSON output.
- **Unit Seam (Grounded Quote Validation Seam)**: Testing the `EvidenceValidator` against exact matches, whitespace drift, punctuation variations, and fabricated quotes to ensure 100% precision.
- **Evaluation Seam (`evaluation/evaluate.py`)**: End-to-end evaluation measuring:
  - Retrieval recall & precision on standard interview guide questions
  - Quote exactness (Levenshtein distance = 0 against canonical text)
  - Timestamp integrity (matches canonical seconds)
  - Groundedness score on synthesized responses

---

## Out of Scope
- Custom vector databases (Pinecone, Chroma, Qdrant, Milvus, pgvector) — per explicit case study instructions to use Google File Search.
- Audio/video playback media streams — no audio files are provided; timestamps are displayed as evidence references without fabricating media URLs.
- Multi-agent swarm protocols with complex negotiation — simplicity and deterministic routing are prioritized per requirement #7.

---

## Further Notes
- System is designed with an offline deterministic fallback mode for immediate local testing and evaluation even when `GEMINI_API_KEY` is not present, while seamlessly activating live Gemini + File Search when the key is configured.
- Comprehensive `README.md` includes Mermaid architecture diagram, tradeoffs explanation, and 5-step video demo guide.
