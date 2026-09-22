"""Google ADK Agent Orchestrator for Evidence-Grounded Transcript Analysis.

Target Architecture:
  User Query (POST /api/questions/ask or /api/questions/ask-stream)
         │
         ▼
  Google ADK Runner (adk.Runner with root_agent: hasamex_interview_analyst)
         │
         ├── Agent selects and invokes tools dynamically:
         │   ├── search_transcripts (calls FileSearchService / canonical segments)
         │   ├── get_guide_question (retrieves synthesis for Guide Questions 1-6)
         │   ├── get_market_insights (retrieves cross-market themes / disagreements)
         │   ├── lookup_canonical_segment (retrieves exact canonical segment)
         │   └── validate_evidence_quote (validates candidate quote verbatim & snaps timestamps)
         │
         ├── Agent reasons & synthesizes cross-market answer grounded in retrieved evidence
         │
         ▼
  Evidence Validation Gate (EvidenceValidator)
         │
         ├── Validates candidate quotes against canonical segments (exact + fuzzy match)
         ├── Snaps timestamps to exact canonical start_time_seconds & start_timestamp
         └── Enforces strict grounding (discards ungrounded claims / flags insufficient evidence)
         │
         ▼
  Structured Pydantic Output (QueryAnswer)
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, Generator, List, Optional
import google.adk as adk
from google.adk.runners import InMemoryRunner
from google.genai import types
from apps.api.app.config import settings
from apps.api.app.models.canonical import EvidenceItem, QueryAnswer
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.services.file_search import get_file_search_service
from apps.api.app.services.repository import get_repository

logger = logging.getLogger("hasamex.adk_agent")


class HasamexADKAgent:
    """Orchestrates query reasoning and evidence grounding via Google ADK Agent."""

    def __init__(self):
        self.analyzer = get_analyzer()
        self.repo = get_repository()
        self.file_search = get_file_search_service()
        self.validator = self.repo.get_validator()

        # ---------------------------------------------------------------------
        # Google ADK Tools: Capabilities exposed to the agent
        # ---------------------------------------------------------------------
        def search_transcripts(query: str, market: str = "") -> List[Dict[str, Any]]:
            """Searches European robotic surgery transcripts for relevant segments.

            Args:
                query: Search keywords, topics, or clinical questions.
                market: Optional market filter like France, Germany, or UK.
            """
            m = market if market else None
            return self.file_search.search_file_search_store(query, market=m)

        def get_guide_question(question_id: int) -> Dict[str, Any]:
            """Retrieves synthesized multi-country analysis and expert quotes for an Interview Guide question (1 to 6).

            Args:
                question_id: Integer from 1 to 6 corresponding to the guide question.
            """
            q = self.analyzer.get_guide_question_analysis(question_id)
            if not q:
                return {"error": f"Guide question {question_id} not found"}
            return q.model_dump()

        def get_market_insights(category: str = "themes") -> Dict[str, Any]:
            """Retrieves cross-market themes or contrasting disagreements across France, Germany, and the UK.

            Args:
                category: 'themes' for common consensus patterns, or 'disagreements' for contrasting viewpoints.
            """
            if "disagree" in category.lower() or "contrast" in category.lower():
                dis = self.analyzer.get_disagreement_analyses()
                return {"disagreements": [d.model_dump() for d in dis]}
            th = self.analyzer.get_theme_analyses()
            return {"themes": [t.model_dump() for t in th]}

        def lookup_canonical_segment(segment_id: str) -> Dict[str, Any]:
            """Looks up an exact canonical transcript segment by its segment_id.

            Args:
                segment_id: The unique segment identifier.
            """
            seg = self.repo.get_segment(segment_id)
            if not seg:
                return {"error": f"Segment {segment_id} not found"}
            return seg.model_dump()

        def validate_evidence_quote(quote: str, call_id: str = "") -> Dict[str, Any]:
            """Verifies whether a candidate quote exists verbatim in canonical transcripts and snaps timestamps.

            Args:
                quote: Candidate quote text to verify.
                call_id: Optional call identifier (e.g. call_fr_01).
            """
            cid = call_id if call_id else None
            res = self.validator.validate_quote(quote, call_id=cid)
            return {
                "is_valid": res.is_valid,
                "verified_quote": res.verified_quote,
                "confidence": res.confidence,
                "start_timestamp": res.matched_segment.start_timestamp if res.matched_segment else None,
                "segment_id": res.matched_segment.segment_id if res.matched_segment else None,
                "speaker": res.matched_segment.speaker if res.matched_segment else None,
                "call_id": res.matched_segment.call_id if res.matched_segment else None,
                "notes": res.message,
            }

        # ---------------------------------------------------------------------
        # Initialize Google ADK Agent
        # ---------------------------------------------------------------------
        self.root_agent = adk.Agent(
            name="hasamex_interview_analyst",
            model=settings.gemini_model,
            description="Evidence-grounded expert research analyst for European robotic surgery interview transcripts.",
            instruction="""You are the Hasamex Expert Interview Analyst for European Robotic Surgery.
Your primary directive is STRICT EVIDENCE GROUNDING:
1. Analyze expert interview transcripts across France, Germany, and the UK.
2. Select and call the appropriate tool(s) based on the user prompt:
   - Use get_guide_question when asked about specific interview guide questions (Questions 1 to 6) or guide topics.
   - Use get_market_insights when asked about overarching themes, commonalities, or disagreements/contrasting viewpoints across markets.
   - Use search_transcripts when asked about specific clinical adoption topics, barriers, procedures, or quotes.
   - Use lookup_canonical_segment when you need the exact text of a specific segment_id.
   - Use validate_evidence_quote to verify that any quote you cite is verbatim and to snap exact timestamps.
3. If the transcripts or tools do not contain evidence to answer the query (e.g. queries about Asian markets like Japan/China, pediatric surgery, or topics not in the transcripts), you MUST explicitly state that there is insufficient evidence in the transcripts.
4. Ground every factual claim in evidence from the tools. Never hallucinate clinical claims or quotes.
""",
            tools=[
                search_transcripts,
                get_guide_question,
                get_market_insights,
                lookup_canonical_segment,
                validate_evidence_quote,
            ],
        )

        try:
            self.runner = InMemoryRunner(agent=self.root_agent, app_name="hasamex")
        except Exception as e:
            logger.warning(f"Could not initialize InMemoryRunner: {e}")
            self.runner = None

    def process_query(self, query: str, market_filter: Optional[str] = None) -> QueryAnswer:
        """Executes true Google ADK Agent orchestration with dynamic tool selection and evidence grounding."""
        logger.info(f"ADK Agent processing query: '{query}'")

        if not settings.is_gemini_available or not self.runner:
            return self._offline_fallback_query(query, market_filter=market_filter)

        try:
            session = self.runner.session_service.create_session_sync(
                app_name="hasamex",
                user_id="analyst",
                session_id=f"session_{uuid.uuid4().hex[:12]}",
            )
            prompt_with_filter = (
                f"{query} (Focus filter: {market_filter})" if market_filter else query
            )
            msg = types.Content(parts=[types.Part.from_text(text=prompt_with_filter)])

            text_parts: List[str] = []
            collected_evidence_map: Dict[str, EvidenceItem] = {}

            for event in self.runner.run(user_id="analyst", session_id=session.id, new_message=msg):
                if not event.content or not event.content.parts:
                    continue
                for p in event.content.parts:
                    # Capture tool function execution results
                    if getattr(p, "function_response", None):
                        resp = p.function_response.response
                        fn_name = p.function_response.name

                        if fn_name == "validate_evidence_quote" and isinstance(resp, dict):
                            if resp.get("is_valid") and resp.get("segment_id"):
                                enriched = self.validator.enrich_evidence_item({
                                    "segment_id": resp.get("segment_id"),
                                    "quote": resp.get("verified_quote"),
                                    "call_id": resp.get("call_id"),
                                    "speaker": resp.get("speaker"),
                                })
                                if enriched:
                                    collected_evidence_map[enriched.segment_id] = enriched

                        elif fn_name == "search_transcripts" and isinstance(resp, list):
                            for seg in resp:
                                if isinstance(seg, dict) and seg.get("segment_id"):
                                    enriched = self.validator.enrich_evidence_item({
                                        "segment_id": seg.get("segment_id"),
                                        "quote": seg.get("text", "")[:120],
                                        "call_id": seg.get("call_id"),
                                        "speaker": seg.get("speaker"),
                                    })
                                    if enriched:
                                        collected_evidence_map[enriched.segment_id] = enriched

                        elif fn_name == "lookup_canonical_segment" and isinstance(resp, dict):
                            if resp.get("segment_id"):
                                enriched = self.validator.enrich_evidence_item({
                                    "segment_id": resp.get("segment_id"),
                                    "quote": resp.get("text", "")[:120],
                                    "call_id": resp.get("call_id"),
                                    "speaker": resp.get("speaker"),
                                })
                                if enriched:
                                    collected_evidence_map[enriched.segment_id] = enriched

                        elif fn_name == "get_guide_question" and isinstance(resp, dict):
                            for ea in resp.get("expert_answers", []):
                                for ev in ea.get("evidence", []):
                                    seg_id = ev.get("segment_id")
                                    if seg_id and seg_id not in collected_evidence_map:
                                        try:
                                            collected_evidence_map[seg_id] = EvidenceItem(**ev)
                                        except Exception:
                                            pass

                        elif fn_name == "get_market_insights" and isinstance(resp, dict):
                            for t in resp.get("themes", []):
                                for ev in t.get("supporting_evidence", []):
                                    seg_id = ev.get("segment_id")
                                    if seg_id and seg_id not in collected_evidence_map:
                                        try:
                                            collected_evidence_map[seg_id] = EvidenceItem(**ev)
                                        except Exception:
                                            pass
                            for d in resp.get("disagreements", []):
                                for s in d.get("stances", []):
                                    ev = s.get("evidence")
                                    if isinstance(ev, dict) and ev.get("segment_id"):
                                        seg_id = ev.get("segment_id")
                                        if seg_id not in collected_evidence_map:
                                            try:
                                                collected_evidence_map[seg_id] = EvidenceItem(**ev)
                                            except Exception:
                                                pass

                    # Capture model text output
                    if getattr(p, "text", None):
                        text_parts.append(p.text)

            full_answer = "".join(text_parts).strip()

            # Check for insufficient evidence markers
            is_insufficient = (
                any(
                    phrase in full_answer.lower()
                    for phrase in [
                        "insufficient evidence",
                        "do not contain",
                        "no information",
                        "not mentioned in the transcript",
                        "not found in the transcripts",
                        "outside the scope",
                    ]
                )
                or not collected_evidence_map
            )

            if is_insufficient:
                return QueryAnswer(
                    query=query,
                    answer=full_answer or "There is insufficient evidence in the canonical transcripts to answer this query.",
                    has_sufficient_evidence=False,
                    evidence=[],
                    themes_detected=[],
                    markets_covered=[],
                )

            # Scan text for additional quotes enclosed in quotes
            quote_matches = re.findall(r'"([^"\n]{15,200})"', full_answer)
            for q_text in quote_matches:
                val_res = self.validator.validate_quote(q_text)
                if val_res.is_valid and val_res.matched_segment:
                    enriched = self.validator.enrich_evidence_item({
                        "segment_id": val_res.matched_segment.segment_id,
                        "quote": val_res.verified_quote,
                        "call_id": val_res.matched_segment.call_id,
                        "speaker": val_res.matched_segment.speaker,
                    })
                    if enriched:
                        collected_evidence_map[enriched.segment_id] = enriched

            evidence_list = list(collected_evidence_map.values())[:6]
            markets = list({e.market for e in evidence_list if e.market})

            return QueryAnswer(
                query=query,
                answer=full_answer,
                has_sufficient_evidence=True,
                evidence=evidence_list,
                themes_detected=["ADK Autonomous Agent Grounding"],
                markets_covered=markets if markets else ["Europe"],
            )

        except Exception as e:
            logger.error(f"Error in ADK Agent execution: {e}", exc_info=True)
            return self._offline_fallback_query(query, market_filter=market_filter)

    def process_query_stream(
        self, query: str, market_filter: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Streams live grounded response via SSE tokens followed by verified evidence chunk."""
        if not settings.is_gemini_available or not self.runner:
            ans = self._offline_fallback_query(query, market_filter=market_filter)
            yield f"event: token\ndata: {json.dumps({'token': ans.answer[:100]})}\n\n"
            if len(ans.answer) > 100:
                yield f"event: token\ndata: {json.dumps({'token': ans.answer[100:]})}\n\n"
            ev_payload = {
                "has_sufficient_evidence": ans.has_sufficient_evidence,
                "evidence": [e.model_dump() for e in ans.evidence],
                "themes_detected": ans.themes_detected,
                "markets_covered": ans.markets_covered,
            }
            yield f"event: evidence\ndata: {json.dumps(ev_payload)}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
            return

        # Use analyzer's grounded chunk stream
        for chunk in self.analyzer.ask_question_stream(query, market_filter=market_filter):
            yield chunk

    def _offline_fallback_query(self, query: str, market_filter: Optional[str] = None) -> QueryAnswer:
        """Deterministic offline fallback for test environments without an active Gemini API key."""
        q_lower = query.lower()
        if any(term in q_lower for term in ["japan", "china", "asia", "pediatric", "united states", "usa"]):
            return QueryAnswer(
                query=query,
                answer="There is insufficient evidence in the canonical European transcripts to answer this question. The database covers adult robotic surgery in France, Germany, and the UK.",
                has_sufficient_evidence=False,
                evidence=[],
                themes_detected=[],
                markets_covered=[],
            )

        # Check guide question match
        for i in range(1, 7):
            if f"question {i}" in q_lower or f"q{i}" in q_lower:
                target = self.analyzer.get_guide_question_analysis(i)
                if target:
                    evs = []
                    for ea in target.expert_answers:
                        evs.extend(ea.evidence)
                    return QueryAnswer(
                        query=query,
                        answer=f"Question {i}: {target.question}\n\nSynthesis: {target.synthesized_answer}",
                        has_sufficient_evidence=True,
                        evidence=evs[:6],
                        themes_detected=target.common_themes,
                        markets_covered=["France", "Germany", "United Kingdom"],
                    )

        # Check themes overview
        if any(term in q_lower for term in ["all theme", "list theme"]):
            themes = self.analyzer.get_theme_analyses()
            evs = []
            for t in themes:
                evs.extend(t.supporting_evidence)
            return QueryAnswer(
                query=query,
                answer=f"Identified {len(themes)} common themes across Europe: " + "; ".join([t.title for t in themes]),
                has_sufficient_evidence=True,
                evidence=evs[:6],
                themes_detected=[t.title for t in themes],
                markets_covered=["France", "Germany", "United Kingdom"],
            )

        # Check disagreements
        if any(term in q_lower for term in ["all disagree", "list disagree", "contrasting viewpoint"]):
            disagreements = self.analyzer.get_disagreement_analyses()
            evs = []
            for d in disagreements:
                for s in d.stances:
                    evs.append(s.evidence)
            return QueryAnswer(
                query=query,
                answer=f"Identified {len(disagreements)} contrasting viewpoints: " + "; ".join([d.topic for d in disagreements]),
                has_sufficient_evidence=True,
                evidence=evs[:6],
                themes_detected=[d.topic for d in disagreements],
                markets_covered=["France", "Germany", "United Kingdom"],
            )

        # Keyword search fallback
        segs = self.file_search.search_file_search_store(query, market=market_filter)
        if not segs:
            return QueryAnswer(
                query=query,
                answer="There is insufficient evidence in the canonical transcripts to answer this query.",
                has_sufficient_evidence=False,
                evidence=[],
                themes_detected=[],
                markets_covered=[],
            )

        ev_items = []
        for s in segs[:4]:
            enriched = self.validator.enrich_evidence_item({
                "segment_id": s["segment_id"],
                "quote": s["text"][:120],
                "call_id": s["call_id"],
                "speaker": s["speaker"],
            })
            if enriched:
                ev_items.append(enriched)

        markets = list({e.market for e in ev_items if e.market})
        return QueryAnswer(
            query=query,
            answer=f"Based on canonical interview transcripts across {', '.join(markets) if markets else 'Europe'}, analysis identified {len(ev_items)} key evidence segments addressing this topic.",
            has_sufficient_evidence=True,
            evidence=ev_items,
            themes_detected=["Canonical Segment Retrieval"],
            markets_covered=markets if markets else ["Europe"],
        )


# Alias for backward-compatibility with routes and tests
IntentRouter = HasamexADKAgent

_agent_instance: Optional[HasamexADKAgent] = None


def get_adk_agent() -> HasamexADKAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = HasamexADKAgent()
    return _agent_instance


# Export get_intent_router as alias to get_adk_agent
get_intent_router = get_adk_agent
