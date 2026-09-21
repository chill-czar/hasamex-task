"""Live Google Cloud Gemini Grounded Analysis Engine.

Zero hardcoded answers: 100% of analytical answers, themes, disagreements,
and Q&A responses are generated dynamically by Google Cloud Gemini (gemini-3.6-flash)
and grounded against the authoritative PostgreSQL/SQLite canonical database via EvidenceValidator.
"""

import hashlib
import json
import logging
import re
from typing import List, Optional, Dict, Any
from google.genai import types
from apps.api.app.config import settings
from apps.api.app.models.canonical import (
    GuideQuestionAnalysis,
    ExpertAnswer,
    EvidenceItem,
    ThemeItem,
    DisagreementItem,
    ExpertStance,
    QueryAnswer,
    DisagreementCategory,
)
from apps.api.app.services.repository import CanonicalRepository, get_repository
from apps.api.app.services.file_search import get_file_search_service

logger = logging.getLogger("hasamex.analyzer")

GUIDE_QUESTIONS = {
    1: "How would you describe current adoption of robotic surgery in your market?",
    2: "What are the main barriers to adoption?",
    3: "How important are hospital budgets and ROI in purchasing decisions?",
    4: "How important are surgeon training and clinical outcomes?",
    5: "What adoption trend do you expect over the next 3–5 years?",
    6: "What is the typical hospital decision-making timeline for purchasing a new robotic system?",
}


def compute_content_hash(repository: CanonicalRepository, model: str) -> str:
    """Computes a deterministic hash of canonical transcripts and model version."""
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    for call in repository.get_all_calls():
        h.update(call.call_id.encode("utf-8"))
        for s in call.segments:
            h.update(s.segment_id.encode("utf-8"))
            h.update(s.text.encode("utf-8"))
    return h.hexdigest()[:16]


class GroundedAnalyzer:
    """Analyzes expert transcripts using live Google Cloud Gemini models with canonical evidence grounding."""

    def __init__(self, repository: Optional[CanonicalRepository] = None):
        self.repo = repository or get_repository()
        self.validator = self.repo.get_validator()
        self.file_search = get_file_search_service()
        self.client = None
        self.content_hash = compute_content_hash(self.repo, settings.gemini_model)

        if settings.is_gemini_available:
            try:
                import google.genai as genai
                self.client = genai.Client(api_key=settings.gemini_api_key)
                logger.info(f"Initialized Google GenAI Client with model: {settings.gemini_model}")
            except Exception as e:
                logger.error(f"Failed to initialize live GenAI client: {e}")

        # In-memory session caches to avoid re-billing identical calls in the same user session
        self._guide_analyses_cache: Dict[int, GuideQuestionAnalysis] = {}
        self._themes_cache: Optional[List[ThemeItem]] = None
        self._disagreements_cache: Optional[List[DisagreementItem]] = None

        # Warm memory cache immediately from persisted database if available
        self.warm_cache()

    def warm_cache(self) -> None:
        """Loads all precomputed analyses from the database into memory if content hash matches."""
        try:
            all_mat = self.repo.get_all_materialized_analyses()
            loaded_count = 0
            for key, record in all_mat.items():
                if record["content_hash"] != self.content_hash:
                    continue
                payload = json.loads(record["payload_json"])
                if key.startswith("guide_q"):
                    try:
                        q_id = int(key.replace("guide_q", ""))
                        self._guide_analyses_cache[q_id] = GuideQuestionAnalysis.model_validate(payload)
                        loaded_count += 1
                    except Exception as e:
                        logger.warning(f"Error deserializing cached {key}: {e}")
                elif key == "themes":
                    try:
                        self._themes_cache = [ThemeItem.model_validate(item) for item in payload]
                    except Exception as e:
                        logger.warning(f"Error deserializing cached themes: {e}")
                elif key == "disagreements":
                    try:
                        self._disagreements_cache = [DisagreementItem.model_validate(item) for item in payload]
                    except Exception as e:
                        logger.warning(f"Error deserializing cached disagreements: {e}")

            if loaded_count > 0 or self._themes_cache or self._disagreements_cache:
                logger.info(
                    f"Warmed cache from database: {loaded_count}/6 guide questions, "
                    f"themes={'yes' if self._themes_cache else 'no'}, "
                    f"disagreements={'yes' if self._disagreements_cache else 'no'}"
                )
        except Exception as e:
            logger.warning(f"Failed to warm cache from database: {e}")

    def _get_transcripts_context(self, market_filter: Optional[str] = None) -> str:
        """Builds formatted authoritative context from canonical transcript segments."""
        blocks = []
        for call in self.repo.get_all_calls():
            if market_filter and market_filter.lower() not in call.market.lower():
                continue
            expert = self.repo.get_expert(call.expert_id)
            expert_name = expert.name if expert else "Expert"
            expert_role = expert.role if expert else ""
            market = call.market

            header = f"=== CALL_ID: {call.call_id} | EXPERT: {expert_name} ({expert_role}, {market}) ==="
            dialogue = []
            for seg in call.segments:
                dialogue.append(f"[{seg.start_timestamp}] {seg.speaker}: {seg.text}")
            blocks.append(header + "\n" + "\n".join(dialogue))
        return "\n\n".join(blocks)

    def get_interview_guide_analyses(self, force_refresh: bool = False) -> List[GuideQuestionAnalysis]:
        """Analyzes all 6 interview guide questions using live Google Cloud Gemini reasoning."""
        analyses = []
        for q_id in range(1, 7):
            analysis = self.get_guide_question_analysis(q_id, force_refresh=force_refresh)
            if analysis:
                analyses.append(analysis)
        return analyses

    def get_guide_question_analysis(self, question_id: int, force_refresh: bool = False) -> Optional[GuideQuestionAnalysis]:
        """Analyzes a single interview guide question dynamically using live Google Cloud Gemini."""
        if not force_refresh:
            if question_id in self._guide_analyses_cache:
                return self._guide_analyses_cache[question_id]
            cached = self.repo.get_materialized_analysis(f"guide_q{question_id}")
            if cached and cached["content_hash"] == self.content_hash:
                try:
                    analysis = GuideQuestionAnalysis.model_validate(json.loads(cached["payload_json"]))
                    self._guide_analyses_cache[question_id] = analysis
                    return analysis
                except Exception as e:
                    logger.warning(f"Error restoring cached guide_q{question_id}: {e}")

        question_text = GUIDE_QUESTIONS.get(question_id)
        if not question_text:
            return None

        if not self.client:
            raise RuntimeError("Google GenAI client is not configured. Please set GEMINI_API_KEY in .env")

        context = self._get_transcripts_context()

        prompt = f"""You are an evidence-grounded healthcare research analyst for the Hasamex European Robotic Surgery study.
Transcripts from 3 expert interviews (France, Germany, United Kingdom) are provided below.

Task: Answer Interview Guide Question {question_id}:
"{question_text}"

Instructions:
1. Synthesize the findings across all 3 markets (France, Germany, UK) into a clear synthesized_answer.
2. For each expert (Dr. Jean Martin in France, Anna Keller in Germany, Dr. Emily Carter in UK):
   - summarize their perspective
   - extract their exact verbatim quote spoken in the transcript
3. Identify common consensus themes and contrasting viewpoints.
4. Output valid JSON matching this schema:
{{
  "synthesized_answer": "Overall market synthesis across France, Germany, and UK...",
  "expert_answers": [
    {{
      "expert_id": "expert_fr_martin",
      "expert_name": "Dr. Jean Martin",
      "market": "France",
      "role": "Head of Urology",
      "perspective_summary": "Summary of French perspective...",
      "quote": "Exact verbatim quote from Dr. Martin..."
    }},
    {{
      "expert_id": "expert_de_keller",
      "expert_name": "Anna Keller",
      "market": "Germany",
      "role": "Former Hospital Procurement Director",
      "perspective_summary": "Summary of German perspective...",
      "quote": "Exact verbatim quote from Anna Keller..."
    }},
    {{
      "expert_id": "expert_gb_carter",
      "expert_name": "Dr. Emily Carter",
      "market": "United Kingdom",
      "role": "Consultant Urologist",
      "perspective_summary": "Summary of UK perspective...",
      "quote": "Exact verbatim quote from Dr. Carter..."
    }}
  ],
  "common_themes": ["Theme 1", "Theme 2"],
  "contrasting_viewpoints": ["Contrasting point 1"]
}}

Transcripts:
{context}
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        raw_json = json.loads(response.text)
        synthesized_answer = raw_json.get("synthesized_answer", "")
        common_themes = raw_json.get("common_themes", [])
        contrasting_viewpoints = raw_json.get("contrasting_viewpoints", [])

        validated_expert_answers: List[ExpertAnswer] = []
        for ea in raw_json.get("expert_answers", []):
            quote_raw = ea.get("quote", "")
            exp_id = ea.get("expert_id")
            # Strictly validate quote against canonical transcripts in DB
            enriched = self.validator.enrich_evidence_item({
                "quote": quote_raw,
                "expert_id": exp_id,
                "relevance": f"Statement by {ea.get('expert_name')} on {question_text}",
            })

            evidence_list = [enriched] if enriched else []
            if not evidence_list:
                # If slight variation, find matching segment in DB and use exact text
                val_res = self.validator.validate_quote(quote_raw, expert_id=exp_id)
                if val_res.matched_segment:
                    seg = val_res.matched_segment
                    evidence_list = [
                        EvidenceItem(
                            segment_id=seg.segment_id,
                            call_id=seg.call_id,
                            expert_id=seg.expert_id,
                            expert_name=ea.get("expert_name", seg.speaker),
                            speaker=seg.speaker,
                            market=ea.get("market", "Europe"),
                            quote=seg.text,
                            start_timestamp=seg.start_timestamp,
                            end_timestamp=seg.end_timestamp,
                            start_time_seconds=seg.start_time_seconds,
                            end_time_seconds=seg.end_time_seconds,
                            relevance=f"Canonical segment for {question_text}",
                            verified=True,
                            validation_notes="Verified against canonical segment",
                        )
                    ]

            validated_expert_answers.append(
                ExpertAnswer(
                    expert_id=ea.get("expert_id", "unknown"),
                    expert_name=ea.get("expert_name", "Expert"),
                    market=ea.get("market", "Europe"),
                    role=ea.get("role", "Healthcare Professional"),
                    has_evidence=len(evidence_list) > 0,
                    perspective_summary=ea.get("perspective_summary", ""),
                    evidence=evidence_list,
                )
            )

        analysis = GuideQuestionAnalysis(
            question_id=question_id,
            question=question_text,
            synthesized_answer=synthesized_answer,
            expert_answers=validated_expert_answers,
            common_themes=common_themes,
            contrasting_viewpoints=contrasting_viewpoints,
        )

        self._guide_analyses_cache[question_id] = analysis
        try:
            self.repo.save_materialized_analysis(
                f"guide_q{question_id}",
                self.content_hash,
                analysis.model_dump_json(),
            )
        except Exception as e:
            logger.warning(f"Failed to persist materialized guide_q{question_id}: {e}")
        return analysis

    def get_theme_analyses(self, force_refresh: bool = False) -> List[ThemeItem]:
        """Identifies common themes across all 3 transcripts using live Google Cloud Gemini reasoning."""
        if not force_refresh:
            if self._themes_cache is not None:
                return self._themes_cache
            cached = self.repo.get_materialized_analysis("themes")
            if cached and cached["content_hash"] == self.content_hash:
                try:
                    themes = [ThemeItem.model_validate(item) for item in json.loads(cached["payload_json"])]
                    self._themes_cache = themes
                    return themes
                except Exception as e:
                    logger.warning(f"Error restoring cached themes: {e}")

        if not self.client:
            raise RuntimeError("Google GenAI client is not configured. Please set GEMINI_API_KEY in .env")

        context = self._get_transcripts_context()

        prompt = f"""You are an evidence-grounded research analyst.
Examine the 3 European robotic surgery transcripts (France, Germany, UK) below.
Identify the 4 major common themes across the interviews where multiple experts share common dynamics.

For each theme:
1. Provide a title and detailed summary.
2. List the markets and experts mentioning this theme.
3. For each expert, provide their exact verbatim quote from the transcript.

Return ONLY valid JSON adhering strictly to this schema:
{{
  "themes": [
    {{
      "theme_id": "theme_01",
      "title": "Theme Title",
      "summary": "Detailed summary...",
      "markets": ["France", "Germany", "United Kingdom"],
      "experts": ["Dr. Jean Martin", "Anna Keller", "Dr. Emily Carter"],
      "supporting_evidence": [
        {{
          "call_id": "call_fr_01",
          "expert_id": "expert_fr_martin",
          "expert_name": "Dr. Jean Martin",
          "quote": "Exact verbatim quote from Dr. Martin..."
        }},
        {{
          "call_id": "call_de_02",
          "expert_id": "expert_de_keller",
          "expert_name": "Anna Keller",
          "quote": "Exact verbatim quote from Anna Keller..."
        }},
        {{
          "call_id": "call_uk_03",
          "expert_id": "expert_gb_carter",
          "expert_name": "Dr. Emily Carter",
          "quote": "Exact verbatim quote from Dr. Carter..."
        }}
      ]
    }}
  ]
}}

Transcripts:
{context}
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        raw_json = json.loads(response.text)
        themes: List[ThemeItem] = []

        for raw_t in raw_json.get("themes", []):
            validated_evidence = []
            for ev in raw_t.get("supporting_evidence", []):
                enriched = self.validator.enrich_evidence_item({
                    "quote": ev.get("quote", ""),
                    "call_id": ev.get("call_id"),
                    "expert_id": ev.get("expert_id"),
                    "relevance": f"Supporting quote for {raw_t.get('title')}",
                })
                if enriched:
                    validated_evidence.append(enriched)

            themes.append(
                ThemeItem(
                    theme_id=raw_t.get("theme_id", "theme_gen"),
                    title=raw_t.get("title", ""),
                    summary=raw_t.get("summary", ""),
                    markets=raw_t.get("markets", ["France", "Germany", "United Kingdom"]),
                    experts=raw_t.get("experts", []),
                    supporting_evidence=validated_evidence,
                )
            )

        self._themes_cache = themes
        try:
            payload = json.dumps([t.model_dump() for t in themes])
            self.repo.save_materialized_analysis("themes", self.content_hash, payload)
        except Exception as e:
            logger.warning(f"Failed to persist themes: {e}")
        return themes

    def get_disagreement_analyses(self, force_refresh: bool = False) -> List[DisagreementItem]:
        """Identifies contrasting viewpoints across interviews using live Google Cloud Gemini reasoning."""
        if not force_refresh:
            if self._disagreements_cache is not None:
                return self._disagreements_cache
            cached = self.repo.get_materialized_analysis("disagreements")
            if cached and cached["content_hash"] == self.content_hash:
                try:
                    disagreements = [DisagreementItem.model_validate(item) for item in json.loads(cached["payload_json"])]
                    self._disagreements_cache = disagreements
                    return disagreements
                except Exception as e:
                    logger.warning(f"Error restoring cached disagreements: {e}")

        if not self.client:
            raise RuntimeError("Google GenAI client is not configured. Please set GEMINI_API_KEY in .env")

        context = self._get_transcripts_context()

        prompt = f"""You are an evidence-grounded research analyst.
Examine the 3 European robotic surgery transcripts (France, Germany, UK) below.
Identify the 4 key contrasting viewpoints, disagreements, or differing emphases among the experts.

Classify each disagreement into one of these exact categories:
- "Agreement"
- "Partial agreement"
- "Different emphasis"
- "Contradiction"
- "Unique viewpoint"

For each disagreement:
1. topic and category
2. analytical explanation of the difference
3. the diverging stances with expert name, market, their position, and their exact verbatim quote.

Return ONLY valid JSON adhering strictly to this schema:
{{
  "disagreements": [
    {{
      "topic_id": "disagree_01",
      "topic": "Topic Name",
      "category": "Different emphasis",
      "explanation": "Analytical explanation...",
      "stances": [
        {{
          "expert_id": "expert_de_keller",
          "expert_name": "Anna Keller",
          "market": "Germany",
          "position": "Summary of position...",
          "quote": "Exact verbatim quote...",
          "call_id": "call_de_02"
        }},
        {{
          "expert_id": "expert_gb_carter",
          "expert_name": "Dr. Emily Carter",
          "market": "United Kingdom",
          "position": "Summary of position...",
          "quote": "Exact verbatim quote...",
          "call_id": "call_uk_03"
        }}
      ]
    }}
  ]
}}

Transcripts:
{context}
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        raw_json = json.loads(response.text)
        disagreements: List[DisagreementItem] = []

        for raw_d in raw_json.get("disagreements", []):
            stances: List[ExpertStance] = []
            for st in raw_d.get("stances", []):
                enriched = self.validator.enrich_evidence_item({
                    "quote": st.get("quote", ""),
                    "call_id": st.get("call_id"),
                    "expert_id": st.get("expert_id"),
                    "relevance": f"Stance on {raw_d.get('topic')}",
                })
                if enriched:
                    stances.append(
                        ExpertStance(
                            expert_id=st.get("expert_id", "unknown"),
                            expert_name=st.get("expert_name", "Expert"),
                            market=st.get("market", "Europe"),
                            position=st.get("position", ""),
                            evidence=enriched,
                        )
                    )

            cat_str = raw_d.get("category", "Different emphasis")
            valid_cat = DisagreementCategory.DIFFERENT_EMPHASIS
            for c in DisagreementCategory:
                if c.value.lower() in cat_str.lower():
                    valid_cat = c
                    break

            disagreements.append(
                DisagreementItem(
                    topic_id=raw_d.get("topic_id", "disagree_gen"),
                    topic=raw_d.get("topic", ""),
                    category=valid_cat,
                    explanation=raw_d.get("explanation", ""),
                    stances=stances,
                )
            )

        self._disagreements_cache = disagreements
        try:
            payload = json.dumps([d.model_dump() for d in disagreements])
            self.repo.save_materialized_analysis("disagreements", self.content_hash, payload)
        except Exception as e:
            logger.warning(f"Failed to persist disagreements: {e}")
        return disagreements

    def _build_qa_prompt(self, query: str, full_context: str, streaming: bool = False) -> str:
        """Constructs a clean, evidence-grounded prompt without redundant prompt-stuffing."""
        evidence_instruction = (
            "When finished answering, output on a new line:\n"
            "===EVIDENCE===\n"
            "followed immediately by a JSON object:\n"
            "{\n"
            '  "has_sufficient_evidence": true,\n'
            '  "supporting_quotes": [\n'
            "    {\n"
            '      "call_id": "call_fr_01",\n'
            '      "speaker": "Dr. Martin",\n'
            '      "quote": "Exact verbatim quote from the transcript...",\n'
            '      "relevance": "Why this quote supports the answer"\n'
            "    }\n"
            "  ],\n"
            '  "themes_detected": ["Theme 1"],\n'
            '  "markets_covered": ["France", "Germany"]\n'
            "}"
            if streaming
            else (
                "Output valid JSON adhering strictly to this schema:\n"
                "{\n"
                '  "answer": "Direct factual answer synthesized from transcripts...",\n'
                '  "has_sufficient_evidence": true,\n'
                '  "supporting_quotes": [\n'
                "    {\n"
                '      "call_id": "call_fr_01",\n'
                '      "speaker": "Dr. Martin",\n'
                '      "quote": "Exact verbatim quote from the transcript...",\n'
                '      "relevance": "Why this quote supports the answer"\n'
                "    }\n"
                "  ],\n"
                '  "themes_detected": ["Theme 1"],\n'
                '  "markets_covered": ["France", "Germany"]\n'
                "}"
            )
        )

        return f"""You are an evidence-grounded expert interview analyst.
Answer the user's research question based SOLELY on the European robotic surgery interview transcripts (France, Germany, UK) provided below.

User Question: "{query}"

Full Authoritative Transcripts:
{full_context}

Instructions:
1. Provide a direct, factual synthesis that directly answers the user's question.
2. If the transcripts do not contain sufficient evidence to answer the question (e.g. topic is outside France/Germany/UK robotic surgery, or discusses other countries/specialties not mentioned in the transcripts), state clearly that the transcripts do not contain information on this topic, and set "has_sufficient_evidence" to false.
3. When evidence exists, extract exact verbatim quotes spoken by the experts and provide the call_id and speaker.
4. {evidence_instruction}
"""

    def ask_question(self, query: str, market_filter: Optional[str] = None) -> QueryAnswer:
        """Answers an arbitrary user question using live Google Cloud Gemini reasoning grounded in transcripts."""
        if not self.client:
            raise RuntimeError("Google GenAI client is not configured. Please set GEMINI_API_KEY in .env")

        full_context = self._get_transcripts_context(market_filter=market_filter)
        prompt = self._build_qa_prompt(query, full_context, streaming=False)

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        try:
            raw_text = (response.text or "").strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_json = json.loads(raw_text.strip())
        except Exception as e:
            logger.warning(f"Error parsing json from Gemini response: {e}")
            ans_m = re.search(r'"answer":\s*"((?:\\.|[^"\\])*)"', response.text or "")
            if ans_m:
                try:
                    ans_val = json.loads(f'"{ans_m.group(1)}"')
                except Exception:
                    ans_val = ans_m.group(1)
            else:
                ans_val = response.text or ""

            # Robust fallback quote extraction from raw text
            extracted_quotes = []
            for qm in re.finditer(r'"quote":\s*"((?:\\.|[^"\\])*)"', response.text or ""):
                try:
                    q_text = json.loads(f'"{qm.group(1)}"')
                except Exception:
                    q_text = qm.group(1)
                extracted_quotes.append({"quote": q_text})

            has_ev = '"has_sufficient_evidence": false' not in (response.text or "").lower()
            raw_json = {
                "has_sufficient_evidence": has_ev,
                "answer": ans_val,
                "supporting_quotes": extracted_quotes,
            }

        has_evidence = raw_json.get("has_sufficient_evidence", True)
        answer_text = raw_json.get("answer", "")

        if not has_evidence:
            return QueryAnswer(
                query=query,
                answer=answer_text,
                has_sufficient_evidence=False,
                evidence=[],
                themes_detected=[],
                markets_covered=[],
            )

        validated_evidence: List[EvidenceItem] = []
        for sq in raw_json.get("supporting_quotes", []):
            enriched = self.validator.enrich_evidence_item({
                "quote": sq.get("quote", ""),
                "call_id": sq.get("call_id"),
                "speaker": sq.get("speaker"),
                "relevance": sq.get("relevance"),
            })
            if enriched:
                validated_evidence.append(enriched)

        # Fallback to search if LLM quotes failed validation
        if not validated_evidence and has_evidence:
            fallback_matches = self.file_search.search_file_search_store(query, market=market_filter)
            for seg in fallback_matches[:3]:
                enriched = self.validator.enrich_evidence_item({
                    "quote": seg.get("text", "")[:120],
                    "call_id": seg.get("call_id"),
                    "speaker": seg.get("speaker"),
                    "relevance": "Retrieved context segment",
                })
                if enriched:
                    validated_evidence.append(enriched)

        markets = list({e.market for e in validated_evidence})

        return QueryAnswer(
            query=query,
            answer=answer_text,
            has_sufficient_evidence=True,
            evidence=validated_evidence,
            themes_detected=raw_json.get("themes_detected", ["Live Grounded Retrieval"]),
            markets_covered=markets if markets else ["Europe"],
        )

    def ask_question_stream(self, query: str, market_filter: Optional[str] = None):
        """Streams live grounded response token-by-token followed by verified evidence."""
        if not self.client:
            yield f"event: error\ndata: {json.dumps({'error': 'Google GenAI client is not configured.'})}\n\n"
            return

        full_context = self._get_transcripts_context(market_filter=market_filter)
        prompt = self._build_qa_prompt(query, full_context, streaming=True)

        try:
            stream = self.client.models.generate_content_stream(
                model=settings.gemini_model,
                contents=prompt,
            )

            delimiter = "===EVIDENCE==="
            buffer = ""
            delimiter_found = False
            evidence_buffer = ""

            for chunk in stream:
                chunk_text = chunk.text or ""
                if not chunk_text:
                    continue

                if not delimiter_found:
                    buffer += chunk_text
                    if delimiter in buffer:
                        delimiter_found = True
                        ans, ev = buffer.split(delimiter, 1)
                        if ans:
                            yield f"event: token\ndata: {json.dumps({'token': ans})}\n\n"
                        evidence_buffer += ev
                    else:
                        hold = 0
                        for i in range(1, min(len(buffer), len(delimiter)) + 1):
                            if delimiter.startswith(buffer[-i:]):
                                hold = i
                        if hold > 0:
                            to_emit = buffer[:-hold]
                            buffer = buffer[-hold:]
                        else:
                            to_emit = buffer
                            buffer = ""
                        if to_emit:
                            yield f"event: token\ndata: {json.dumps({'token': to_emit})}\n\n"
                else:
                    evidence_buffer += chunk_text

            if not delimiter_found and buffer:
                delim_match = re.search(r"===+\s*EVIDENCE\s*===+", buffer)
                if delim_match:
                    ans = buffer[:delim_match.start()]
                    ev = buffer[delim_match.end():]
                    if ans:
                        yield f"event: token\ndata: {json.dumps({'token': ans})}\n\n"
                    evidence_buffer += ev
                else:
                    yield f"event: token\ndata: {json.dumps({'token': buffer})}\n\n"

            # Process evidence chunk
            validated_evidence = []
            themes_detected = ["Live Grounded Retrieval"]
            markets_covered = ["Europe"]
            has_evidence = True

            if evidence_buffer.strip():
                try:
                    clean_json_str = evidence_buffer.strip()
                    json_match = re.search(r"\{.*\}", clean_json_str, re.DOTALL)
                    if json_match:
                        raw_json = json.loads(json_match.group(0))
                    else:
                        raw_json = json.loads(clean_json_str)

                    has_evidence = raw_json.get("has_sufficient_evidence", True)
                    themes_detected = raw_json.get("themes_detected", ["Live Grounded Retrieval"])
                    markets_covered = raw_json.get("markets_covered", ["Europe"])

                    for sq in raw_json.get("supporting_quotes", []):
                        enriched = self.validator.enrich_evidence_item({
                            "quote": sq.get("quote", ""),
                            "call_id": sq.get("call_id"),
                            "speaker": sq.get("speaker"),
                            "relevance": sq.get("relevance"),
                        })
                        if enriched:
                            validated_evidence.append(enriched)
                except Exception as parse_err:
                    logger.warning(f"Could not parse evidence JSON from stream: {parse_err}")

            if not validated_evidence and has_evidence:
                fallback_matches = self.file_search.search_file_search_store(query, market=market_filter)
                for seg in fallback_matches[:3]:
                    enriched = self.validator.enrich_evidence_item({
                        "quote": seg.get("text", "")[:120],
                        "call_id": seg.get("call_id"),
                        "speaker": seg.get("speaker"),
                        "relevance": "Retrieved context segment",
                    })
                    if enriched:
                        validated_evidence.append(enriched)

            if validated_evidence:
                markets = list({e.market for e in validated_evidence})
                if markets:
                    markets_covered = markets

            evidence_payload = {
                "has_sufficient_evidence": has_evidence,
                "evidence": [e.model_dump() for e in validated_evidence],
                "themes_detected": themes_detected,
                "markets_covered": markets_covered,
            }
            yield f"event: evidence\ndata: {json.dumps(evidence_payload)}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error during streaming Q&A: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


_analyzer_instance: Optional[GroundedAnalyzer] = None


def get_analyzer() -> GroundedAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = GroundedAnalyzer()
    return _analyzer_instance
