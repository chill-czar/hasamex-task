# 05: Evidence Explorer & Deep-Linking (Interactive Transcript Viewer)

**What to build:**
Full auditability. Implements the `/api/interviews` and `/api/evidence/{segment_id}` endpoints. The Next.js frontend delivers the Evidence Explorer view displaying the full canonical transcripts for all 3 experts. Clicking any citation or timestamp badge anywhere in the platform (Guide, Insights, Q&A) deep-links to this view and highlights the exact segment.

**Blocked by:** 01: Canonical Ingestion, Schema & Evidence Grounding Core

**Status:** ready-for-agent

- [ ] Backend `/api/interviews` and `/api/interviews/{call_id}` endpoints
- [ ] Backend `/api/evidence/{segment_id}` endpoint
- [ ] Next.js Evidence Explorer view with full transcript browser and expert filter
- [ ] Search within transcripts with segment highlighting
- [ ] Cross-app citation link handlers for smooth scroll to highlighted segment
- [ ] Automated tests for evidence explorer
