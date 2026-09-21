"""Evidence verification and grounding validation service."""

import re
import difflib
from typing import List, Optional, Dict, Any
from apps.api.app.models.canonical import Call, Expert, TranscriptSegment, EvidenceItem, ValidationResult


def normalize_text_for_matching(text: str) -> str:
    """Normalize text for robust comparison by standardizing quotes, dashes, and whitespace."""
    if not text:
        return ""
    # Standardize unicode quotes and dashes
    t = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = t.replace("—", "-").replace("–", "-")
    # Replace newlines and multiple spaces with a single space
    t = re.sub(r"\s+", " ", t).strip()
    return t


DEFAULT_MIN_MATCH_RATIO = 0.85
CONTAINED_SEGMENT_CONFIDENCE = 0.98
MAX_COMPARABLE_WORD_DELTA = 15
WINDOW_SIZE_WORD_DELTA = 4
MIN_WINDOW_WORDS = 5


class EvidenceValidator:
    """Validates quotes against canonical transcripts, correcting timestamps and rejecting hallucinations."""

    def __init__(self, calls: List[Call], experts: List[Expert]):
        self.calls = calls
        self.experts = experts
        self.calls_by_id: Dict[str, Call] = {c.call_id: c for c in calls}
        self.experts_by_id: Dict[str, Expert] = {e.expert_id: e for e in experts}

        # Build index of all expert segments
        self.segments_by_id: Dict[str, TranscriptSegment] = {}
        self.segments_by_call: Dict[str, List[TranscriptSegment]] = {}
        self.segments_by_expert: Dict[str, List[TranscriptSegment]] = {}

        for call in calls:
            self.segments_by_call[call.call_id] = call.segments
            for seg in call.segments:
                self.segments_by_id[seg.segment_id] = seg
                if seg.expert_id not in self.segments_by_expert:
                    self.segments_by_expert[seg.expert_id] = []
                self.segments_by_expert[seg.expert_id].append(seg)

    def find_segment_by_id(self, segment_id: str) -> Optional[TranscriptSegment]:
        return self.segments_by_id.get(segment_id)

    def validate_quote(
        self,
        quote: str,
        call_id: Optional[str] = None,
        expert_id: Optional[str] = None,
        min_match_ratio: float = DEFAULT_MIN_MATCH_RATIO,
    ) -> ValidationResult:
        """Validates whether a quote exists in the canonical transcripts."""
        if not quote or not quote.strip():
            return ValidationResult(
                is_valid=False,
                verified_quote="",
                matched_segment=None,
                confidence=0.0,
                message="Quote is empty",
            )

        clean_quote = normalize_text_for_matching(quote.strip(' "\''))
        norm_clean_quote = clean_quote.lower()

        # Determine search candidate segments
        candidate_segments: List[TranscriptSegment] = []
        if call_id and call_id in self.segments_by_call:
            candidate_segments = [s for s in self.segments_by_call[call_id] if s.is_expert]
        elif expert_id and expert_id in self.segments_by_expert:
            candidate_segments = [s for s in self.segments_by_expert[expert_id] if s.is_expert]
        else:
            # Search all expert segments across all calls
            for c in self.calls:
                candidate_segments.extend([s for s in c.segments if s.is_expert])

        # Fast path: literal exact substring in original segment text
        stripped_quote = quote.strip(' "\'')
        for seg in candidate_segments:
            if stripped_quote in seg.text:
                return ValidationResult(
                    is_valid=True,
                    verified_quote=stripped_quote,
                    matched_segment=seg,
                    confidence=1.0,
                    message="Exact verbatim substring verified in canonical transcript",
                )

        # Step 1: Direct normalized substring search
        for seg in candidate_segments:
            seg_norm = normalize_text_for_matching(seg.text)
            if clean_quote in seg_norm or norm_clean_quote in seg_norm.lower():
                # Extract verbatim span from source segment
                start_idx = seg_norm.lower().find(norm_clean_quote)
                end_idx = start_idx + len(clean_quote)
                verbatim_slice = seg_norm[start_idx:end_idx] if start_idx != -1 else seg.text
                return ValidationResult(
                    is_valid=True,
                    verified_quote=verbatim_slice,
                    matched_segment=seg,
                    confidence=1.0,
                    message="Exact verbatim substring verified in canonical transcript",
                )

        # Step 2: Inverted search (if the quote is longer and contains the entire segment)
        for seg in candidate_segments:
            seg_norm = normalize_text_for_matching(seg.text)
            if seg_norm.lower() in norm_clean_quote:
                return ValidationResult(
                    is_valid=True,
                    verified_quote=seg.text,
                    matched_segment=seg,
                    confidence=CONTAINED_SEGMENT_CONFIDENCE,
                    message="Segment text fully contained within candidate quote",
                )

        # Step 3: Sliding window fuzzy matching using SequenceMatcher
        best_ratio = 0.0
        best_seg: Optional[TranscriptSegment] = None
        best_slice: str = ""

        clean_words = clean_quote.split()
        q_len = len(clean_words)

        for seg in candidate_segments:
            seg_norm = normalize_text_for_matching(seg.text)
            seg_words = seg_norm.split()

            # If segment is roughly comparable in length
            if len(seg_words) <= q_len + MAX_COMPARABLE_WORD_DELTA:
                matcher = difflib.SequenceMatcher(None, norm_clean_quote, seg_norm.lower())
                ratio = matcher.ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_seg = seg
                    best_slice = seg.text
            else:
                # Sliding window across longer segment
                window_size = max(MIN_WINDOW_WORDS, min(len(seg_words), q_len + WINDOW_SIZE_WORD_DELTA))
                for w_start in range(0, max(1, len(seg_words) - window_size + 1)):
                    w_words = seg_words[w_start : w_start + window_size]
                    w_text = " ".join(w_words)
                    matcher = difflib.SequenceMatcher(None, norm_clean_quote, w_text.lower())
                    ratio = matcher.ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_seg = seg
                        best_slice = w_text

        if best_ratio >= min_match_ratio and best_seg:
            return ValidationResult(
                is_valid=True,
                verified_quote=best_slice,
                matched_segment=best_seg,
                confidence=round(best_ratio, 3),
                message=f"Fuzzy match verified with confidence {best_ratio:.2f}",
            )

        return ValidationResult(
            is_valid=False,
            verified_quote="",
            matched_segment=None,
            confidence=round(best_ratio, 3),
            message=f"Quote not found in canonical transcripts (best match ratio: {best_ratio:.2f})",
        )

    def enrich_evidence_item(self, raw_item: Any) -> Optional[EvidenceItem]:
        """Validates an evidence item, snaps timestamps to canonical metadata, and returns EvidenceItem."""
        if isinstance(raw_item, dict):
            quote = raw_item.get("quote", "")
            call_id = raw_item.get("call_id")
            expert_id = raw_item.get("expert_id")
            relevance = raw_item.get("relevance")
            segment_id = raw_item.get("segment_id")
        else:
            quote = getattr(raw_item, "quote", "")
            call_id = getattr(raw_item, "call_id", None)
            expert_id = getattr(raw_item, "expert_id", None)
            relevance = getattr(raw_item, "relevance", None)
            segment_id = getattr(raw_item, "segment_id", None)

        # If segment_id was provided directly, verify it exists
        matched_segment: Optional[TranscriptSegment] = None
        if segment_id and segment_id in self.segments_by_id:
            matched_segment = self.segments_by_id[segment_id]

        val_result = self.validate_quote(quote, call_id=call_id, expert_id=expert_id)
        if not val_result.is_valid:
            if matched_segment:
                # Fall back to segment's canonical text
                verified_quote = matched_segment.text
            else:
                return None
        else:
            matched_segment = val_result.matched_segment
            verified_quote = val_result.verified_quote

        if not matched_segment:
            return None

        # Resolve expert and call details
        expert = self.experts_by_id.get(matched_segment.expert_id)
        expert_name = expert.name if expert else matched_segment.speaker
        market = expert.market if expert else "Europe"

        return EvidenceItem(
            segment_id=matched_segment.segment_id,
            call_id=matched_segment.call_id,
            expert_id=matched_segment.expert_id,
            expert_name=expert_name,
            speaker=matched_segment.speaker,
            market=market,
            quote=verified_quote,
            start_timestamp=matched_segment.start_timestamp,
            end_timestamp=matched_segment.end_timestamp,
            start_time_seconds=matched_segment.start_time_seconds,
            end_time_seconds=matched_segment.end_time_seconds,
            relevance=relevance or f"Direct statement by {expert_name}",
            verified=True,
            validation_notes=val_result.message,
        )
