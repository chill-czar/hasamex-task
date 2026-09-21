"""Intent Router for transcript analysis and grounded question answering."""

import logging
from typing import Optional, List
from apps.api.app.services.repository import get_repository
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.models.canonical import QueryAnswer, EvidenceItem

logger = logging.getLogger("hasamex.agent_router")


class IntentRouter:
    """Routes user queries deterministically to materialized syntheses or live Gemini Q&A."""

    INTERVIEW_GUIDE = "INTERVIEW_GUIDE"
    CROSS_CALL_ANALYSIS = "CROSS_CALL_ANALYSIS"
    THEME_ANALYSIS = "THEME_ANALYSIS"
    DISAGREEMENT_ANALYSIS = "DISAGREEMENT_ANALYSIS"
    TRANSCRIPT_QA = "TRANSCRIPT_QA"
    EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"

    def __init__(self):
        self.analyzer = get_analyzer()
        self.repo = get_repository()

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


_router_instance: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance

