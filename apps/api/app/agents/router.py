"""Google ADK Agent and Intent Router for transcript analysis."""

import logging
from typing import Dict, Any, Optional, List
import google.adk as adk
from apps.api.app.services.repository import get_repository
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.models.canonical import QueryAnswer, EvidenceItem

logger = logging.getLogger("hasamex.agent_router")


# Tool definitions for ADK Agent
def transcript_search_tool(query: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches canonical transcript segments matching the query keywords."""
    repo = get_repository()
    words = [w for w in query.lower().split() if len(w) > 3]
    segments = repo.search_segments(words, market=market)
    return [
        {
            "segment_id": s.segment_id,
            "call_id": s.call_id,
            "speaker": s.speaker,
            "start_timestamp": s.start_timestamp,
            "text": s.text,
        }
        for s in segments[:5]
    ]


def evidence_validation_tool(quote: str, call_id: Optional[str] = None) -> Dict[str, Any]:
    """Validates whether a quote verbatim exists in the canonical transcripts."""
    repo = get_repository()
    validator = repo.get_validator()
    res = validator.validate_quote(quote, call_id=call_id)
    return {
        "is_valid": res.is_valid,
        "verified_quote": res.verified_quote,
        "confidence": res.confidence,
        "timestamp": res.matched_segment.start_timestamp if res.matched_segment else None,
    }


class IntentRouter:
    """Routes user queries deterministically or via ADK Agent."""

    INTERVIEW_GUIDE = "INTERVIEW_GUIDE"
    CROSS_CALL_ANALYSIS = "CROSS_CALL_ANALYSIS"
    THEME_ANALYSIS = "THEME_ANALYSIS"
    DISAGREEMENT_ANALYSIS = "DISAGREEMENT_ANALYSIS"
    TRANSCRIPT_QA = "TRANSCRIPT_QA"
    EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"

    def __init__(self):
        self.analyzer = get_analyzer()
        self.repo = get_repository()

        # Initialize Google ADK Agent
        self.root_agent = adk.Agent(
            name="hasamex_interview_analyst",
            description="Expert research assistant that analyzes European robotic surgery transcripts with strict evidence grounding.",
            instruction=(
                "You are an evidence-grounded expert interview analyst. "
                "You may only make factual claims supported by retrieved transcript evidence. "
                "Never fabricate quotes, timestamps, expert names, or transcript content. "
                "When evidence is insufficient, explicitly say so."
            ),
            tools=[transcript_search_tool, evidence_validation_tool],
        )

    def detect_intent(self, query: str) -> str:
        """Deterministic intent detection to eliminate unnecessary LLM calls."""
        q = query.strip().lower()

        if any(term in q for term in ["interview guide", "guide question", "question 1", "question 2", "question 3", "question 4", "question 5", "question 6"]):
            return self.INTERVIEW_GUIDE
        elif any(term in q for term in ["theme", "common theme", "consensus", "shared view"]):
            return self.THEME_ANALYSIS
        elif any(term in q for term in ["disagree", "disagreement", "contrast", "difference", "contrasting", "conflict"]):
            return self.DISAGREEMENT_ANALYSIS
        elif any(term in q for term in ["cross-call", "cross call", "compare expert", "compare markets", "across all"]):
            return self.CROSS_CALL_ANALYSIS
        elif any(term in q for term in ["segment", "lookup quote", "verify quote", "exact quote"]):
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
            analyses = self.analyzer.get_interview_guide_analyses()
            # If a specific question number is referenced, return that
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

            # Return overview of all 6 guide questions
            return QueryAnswer(
                query=query,
                answer=(
                    f"The European Robotic Surgery interview guide comprises {len(analyses)} core questions covering "
                    "current adoption, barriers, budgets/ROI, surgeon training, 3–5 year trends, and hospital purchasing timelines."
                ),
                has_sufficient_evidence=True,
                evidence=[ea.evidence[0] for a in analyses[:3] for ea in a.expert_answers[:1] if ea.evidence],
                themes_detected=["Interview Guide Overview"],
                markets_covered=["France", "Germany", "United Kingdom"],
            )

        # Fallback to grounded Q&A
        return self.analyzer.ask_question(query, market_filter=market_filter)


_router_instance: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance
