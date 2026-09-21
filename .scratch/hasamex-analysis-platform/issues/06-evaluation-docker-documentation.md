# 06: Evaluation Suite, Docker Compose & Production Documentation

**What to build:**
Production verification and demo readiness. Delivers `evaluation/evaluate.py` quantitatively testing retrieval, citation accuracy, verbatim quote match, and groundedness. Provides `docker-compose.yml`, `.env.example`, and a comprehensive `README.md` complete with Mermaid architecture diagrams, system design scaling to 30+ transcripts, and a 5-step video demo walkthrough script.

**Blocked by:** 02, 03, 04, 05

**Status:** ready-for-agent

- [ ] Evaluation dataset `evaluation/benchmark_dataset.json`
- [ ] Evaluation script `evaluation/evaluate.py` testing retrieval, quote exactness, and groundedness
- [ ] `docker-compose.yml` for PostgreSQL and optional backend/frontend services
- [ ] `.env.example` with documented configuration
- [ ] `README.md` with Mermaid architecture, trade-off explanation, 30+ scaling system design, and 5-step video demo script
- [ ] Full test suite execution and verification
