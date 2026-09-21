# 04: Interactive Cross-Transcript Q&A (Google ADK + File Search + UI)

**What to build:**
The interactive query engine: `/api/questions/ask` using Google ADK intent routing and Google File Search Store retrieval with metadata filtering. Responses pass through the post-generation evidence validation gate. Handles insufficient-evidence queries safely. The Next.js frontend delivers the Ask Across Interviews view with answer synthesis, expert tags, and verifiable quote cards.

**Blocked by:** 01: Canonical Ingestion, Schema & Evidence Grounding Core

**Status:** ready-for-agent

- [ ] Google GenAI and Google File Search integration with metadata filtering
- [ ] Google ADK intent routing and orchestration
- [ ] Post-generation EvidenceValidator gate
- [ ] Safe fallback for insufficient evidence
- [ ] Next.js Ask Across Interviews view with query input, suggested questions, and answer cards
- [ ] Automated tests for Q&A
