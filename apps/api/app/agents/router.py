"""Google ADK Agent and Intent Router for evidence-grounded transcript analysis.

Architecture:
  ADK Agent (Identity, Instructions, Tools, Orchestration)
    │
    ▼ (1. Retrieval Tool)
  Canonical Repository & Google Managed File Search Store
    │
    ▼ (2. Reasoning & Synthesis via google-genai SDK)
  Gemini 2.5/3.6 Flash Generation
    │
    ▼ (3. Evidence Validation Tool)
  EvidenceValidator (Verbatim quote matching & timestamp snapping)
    │
    ▼ (4. Structured Output)
  QueryAnswer (Pydantic model)
"""

import logging
from typing import Optional, List, Dict, Any, Generator
import google.adk as adk
from apps.api.app.config import settings
from apps.api.app.services.repository import get_repository
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.models.canonical import QueryAnswer, EvidenceItem

logger = logging.getLogger("hasamex.agent_router")


class IntentRouter:
    """Orchestrates query routing and evidence-grounded analysis via Google ADK Agent."""

    INTERVIEW_GUIDE = "INTERVIEW_GUIDE"
    CROSS_CALL_ANALYSIS = "CROSS_CALL_ANALYSIS"
    THEME_ANALYSIS = "THEME_ANALYSIS"
    DISAGREEMENT_ANALYSIS = "DISAGREEMENT_ANALYSIS"
    TRANSCRIPT_QA = "TRANSCRIPT_QA"
    EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"

    def __init__(self):
        self.analyzer = get_analyzer()
        self.repo = get_repository()

        # ---------------------------------------------------------------------
        # Google ADK Tools: Capabilities exposed to the agent
        # ---------------------------------------------------------------------
        def search_canonical_transcripts(query: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
            """Searches canonical transcript segments matching the query keywords across European markets."""
            words = [w for w in query.lower().split() if len(w) > 3]
            segments = self.repo.search_segments(words, market=market)
            return [
                {
                    "segment_id": s.segment_id,
                    "call_id": s.call_id,
                    "expert_id": s.expert_id,
                    "speaker": s.speaker,
                    "start_timestamp": s.start_timestamp,
                    "end_timestamp": s.end_timestamp,
                    "text": s.text,
                }
                for s in segments[:5]
            ]

        def get_guide_synthesis(question_id: int) -> Dict[str, Any]:
            """Retrieves synthesized cross-market analysis and expert evidence for an interview guide question (1 to 6)."""
            analysis = self.analyzer.get_guide_question_analysis(question_id)
            if not analysis:
                return {"error": f"Guide question {question_id} not found"}
            return analysis.model_dump()

        def get_market_insights(category: str = "themes") -> Dict[str, Any]:
            """Retrieves cross-call common themes or contrasting viewpoints/disagreements across European markets."""
            if "disagree" in category.lower() or "contrast" in category.lower():
                disagreements = self.analyzer.get_disagreement_analyses()
                return {"disagreements": [d.model_dump() for d in disagreements]}
            themes = self.analyzer.get_theme_analyses()
            return {"themes": [t.model_dump() for t in themes]}

        def validate_evidence_quote(quote: str, call_id: Optional[str] = None) -> Dict[str, Any]:
            """Validates whether a candidate quote verbatim exists in canonical transcripts and snaps timestamps."""
            validator = self.repo.get_validator()
            res = validator.validate_quote(quote, call_id=call_id)
            return {
                "is_valid": res.is_valid,
                "verified_quote": res.verified_quote,
                "confidence": res.confidence,
                "timestamp": res.matched_segment.start_timestamp if res.matched_segment else None,
                "notes": res.message,
            }

        # ---------------------------------------------------------------------
        # Initialize Google ADK Agent
        # ---------------------------------------------------------------------
        self.root_agent = adk.Agent(
            name="hasamex_interview_analyst",
            model=settings.gemini_model,
            description="Evidence-grounded expert research assistant analyzing European robotic surgery interview transcripts.",
            instruction="""You are the Hasamex Expert Interview Analyst for European Robotic Surgery.
Your primary directive is STRICT EVIDENCE GROUNDING:
1. Analyze expert interview transcripts across France, Germany, and the UK.
2. Retrieve relevant transcript segments and quotes using available tools.
3. Always validate quotes and timestamps against canonical transcripts.
4. Never fabricate quotes, timestamps, or clinical claims.
5. Explicitly flag when evidence is insufficient.
""",
            tools=[
                search_canonical_transcripts,
                get_guide_synthesis,
                get_market_insights,
                validate_evidence_quote,
            ],
        )

    def detect_intent(self, query: str) -> str:
        """Deterministic intent detection to route explicit structural requests efficiently."""
        q = query.strip().lower()

        # Specific guide questions or general guide query
        if any(term in q for term in ["interview guide", "guide question", "question 1", "question 2", "question 3", "question 4", "question 5", "question 6"]):
            return self.INTERVIEW_GUIDE
        # Explicit overview requests for themes
        elif any(term in q for term in ["all themes", "list themes", "common themes overview", "summary of themes"]):
            return self.THEME_ANALYSIS
        # Explicit overview requests for disagreements
        elif any(term in q for term in ["all disagreements", "list disagreements", "contrasting viewpoints overview"]):
            return self.DISAGREEMENT_ANALYSIS
        # Explicit request for cross-call synthesis
        elif any(term in q for term in ["cross-call overview", "compare all markets", "cross-market summary"]):
            return self.CROSS_CALL_ANALYSIS
        # Direct quote or segment lookup
        elif any(term in q for term in ["lookup quote", "verify quote", "exact quote search"]):
            return self.EVIDENCE_LOOKUP
        return self.TRANSCRIPT_QA

    def process_query(self, query: str, market_filter: Optional[str] = None) -> QueryAnswer:
        """Processes query through intent router and executes grounded analysis."""
        intent = self.detect_intent(query)
        logger.info(f"Routed query '{query}' with intent: {intent}")

        if intent == self.THEME_ANALYSIS:
            themes = self.analyzer.get_theme_analyses()
            theme_titles = [t.title for t in themes]
            all_evidence: List[EvidenceItem] = []
            for t in themes:
                all_evidence.extend(t.supporting_evidence)

            return QueryAnswer(
                query=query,
                answer=(
                    f"Identified {len(themes)} major common themes across France, Germany, and the UK: "
                    + "; ".join([f"({i+1}) {t.title}" for i, t in enumerate(themes)])
                ),
                has_sufficient_evidence=True,
                evidence=all_evidence[:6],
                themes_detected=theme_titles,
                markets_covered=["France", "Germany", "United Kingdom"],
            )

        elif intent == self.DISAGREEMENT_ANALYSIS:
            disagreements = self.analyzer.get_disagreement_analyses()
            disagree_topics = [d.topic for d in disagreements]
            all_evidence: List[EvidenceItem] = []
            for d in disagreements:
                for s in d.stances:
                    all_evidence.append(s.evidence)

            return QueryAnswer(
                query=query,
                answer=(
                    f"Identified {len(disagreements)} key contrasting viewpoints across European markets: "
                    + "; ".join([f"({i+1}) {d.topic} [{d.category}]" for i, d in enumerate(disagreements)])
                ),
                has_sufficient_evidence=True,
                evidence=all_evidence[:6],
                themes_detected=disagree_topics,
                markets_covered=["France", "Germany", "United Kingdom"],
            )

        elif intent == self.INTERVIEW_GUIDE:
            # If a specific question number is referenced, return that precomputed synthesis
            q_num = None
            for i in range(1, 7):
                if f"question {i}" in query.lower() or f"q{i}" in query.lower():
                    q_num = i
                    break

            if q_num:
                target = self.analyzer.get_guide_question_analysis(q_num)
                if target:
                    evs = []
                    for ea in target.expert_answers:
                        evs.extend(ea.evidence)
                    return QueryAnswer(
                        query=query,
                        answer=f"Question {q_num}: {target.question}\n\nSynthesis: {target.synthesized_answer}",
                        has_sufficient_evidence=True,
                        evidence=evs,
                        themes_detected=target.common_themes,
                        markets_covered=["France", "Germany", "United Kingdom"],
                    )

            # Return dynamically generated overview of all 6 guide questions
            return self.analyzer.ask_question(
                "Provide an executive overview synthesizing all 6 interview guide questions for the European Robotic Surgery study.",
                market_filter=market_filter,
            )

        elif intent == self.CROSS_CALL_ANALYSIS:
            return self.analyzer.ask_question(
                f"Synthesize the overarching cross-call themes, differences, and key takeaways across France, Germany, and the UK: {query}",
                market_filter=market_filter,
            )

        elif intent == self.EVIDENCE_LOOKUP:
            words = [w for w in query.lower().split() if len(w) > 3]
            matched_segments = self.repo.search_segments(words, market=market_filter)
            if not matched_segments:
                return QueryAnswer(
                    query=query,
                    answer="No matching canonical transcript segments found for the requested search query.",
                    has_sufficient_evidence=False,
                    evidence=[],
                    themes_detected=[],
                    markets_covered=[],
                )
            evidence_items = []
            validator = self.repo.get_validator()
            for s in matched_segments[:5]:
                enriched = validator.enrich_evidence_item({
                    "segment_id": s.segment_id,
                    "call_id": s.call_id,
                    "speaker": s.speaker,
                    "quote": s.text,
                })
                if enriched:
                    evidence_items.append(enriched)

            return QueryAnswer(
                query=query,
                answer=f"Found {len(evidence_items)} matching canonical transcript segments in the database.",
                has_sufficient_evidence=len(evidence_items) > 0,
                evidence=evidence_items,
                themes_detected=["Direct Canonical Evidence Lookup"],
                markets_covered=list({e.market for e in evidence_items}),
            )

        # Grounded Q&A via analyzer
        return self.analyzer.ask_question(query, market_filter=market_filter)

    def process_query_stream(
        self, query: str, market_filter: Optional[str] = None
    ):
        """Streams grounded token reasoning via SSE followed by verified evidence chunk."""
        for chunk in self.analyzer.ask_question_stream(query, market_filter=market_filter):
            yield chunk


_router_instance: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance

