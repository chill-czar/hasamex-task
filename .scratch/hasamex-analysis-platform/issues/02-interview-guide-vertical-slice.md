# 02: Interview Guide Vertical Slice (Synthesis API + Next.js UI)

**What to build:**
Complete end-to-end workflow for the 6 core questions from `Interview_Guide.txt`. The backend provides `/api/interview-guide` returning synthesized cross-market summaries with multi-expert evidence cards (France, Germany, UK). The Next.js frontend delivers the dedicated Interview Guide view with expandable evidence cards, verbatim quotes, and canonical timestamp badges.

**Blocked by:** 01: Canonical Ingestion, Schema & Evidence Grounding Core

**Status:** ready-for-agent

- [ ] Backend endpoint `/api/interview-guide` and `/api/interview-guide/analyze`
- [ ] Cross-expert synthesis across all 3 countries
- [ ] Verbatim quote citation with canonical timestamps
- [ ] Next.js Interview Guide view with responsive comparative cards
- [ ] Automated tests for guide synthesis
