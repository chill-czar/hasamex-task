"""Canonical data models for the Hasamex Expert Interview Analysis Platform."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DisagreementCategory(str, Enum):
    AGREEMENT = "Agreement"
    PARTIAL_AGREEMENT = "Partial agreement"
    DIFFERENT_EMPHASIS = "Different emphasis"
    CONTRADICTION = "Contradiction"
    UNIQUE_VIEWPOINT = "Unique viewpoint"


class Expert(BaseModel):
    expert_id: str
    name: str
    role: str
    market: str
    country_code: str
    bio: Optional[str] = None


class TranscriptSegment(BaseModel):
    segment_id: str
    call_id: str
    expert_id: str
    speaker: str
    is_expert: bool
    start_time_seconds: float
    end_time_seconds: float
    start_timestamp: str
    end_timestamp: str
    text: str


class Call(BaseModel):
    call_id: str
    expert_id: str
    title: str
    market: str
    source_file: str
    total_duration_seconds: float
    segments: List[TranscriptSegment] = Field(default_factory=list)

    @property
    def segment_count(self) -> int:
        return len(self.segments)


class EvidenceItem(BaseModel):
    segment_id: str
    call_id: str
    expert_id: str
    expert_name: str
    speaker: str
    market: str
    quote: str
    start_timestamp: str
    end_timestamp: str
    start_time_seconds: float
    end_time_seconds: float
    relevance: Optional[str] = None
    verified: bool = True
    validation_notes: Optional[str] = None


class ValidationResult(BaseModel):
    is_valid: bool
    verified_quote: str
    matched_segment: Optional[TranscriptSegment] = None
    confidence: float
    message: str


class ExpertAnswer(BaseModel):
    expert_id: str
    expert_name: str
    market: str
    role: str
    has_evidence: bool = True
    perspective_summary: str
    evidence: List[EvidenceItem] = Field(default_factory=list)


class GuideQuestionAnalysis(BaseModel):
    question_id: int
    question: str
    synthesized_answer: str
    expert_answers: List[ExpertAnswer]
    common_themes: List[str] = Field(default_factory=list)
    contrasting_viewpoints: List[str] = Field(default_factory=list)


class ThemeItem(BaseModel):
    theme_id: str
    title: str
    summary: str
    markets: List[str]
    experts: List[str]
    supporting_evidence: List[EvidenceItem]


class ExpertStance(BaseModel):
    expert_id: str
    expert_name: str
    market: str
    position: str
    evidence: EvidenceItem


class DisagreementItem(BaseModel):
    topic_id: str
    topic: str
    category: DisagreementCategory
    explanation: str
    stances: List[ExpertStance]


class QueryAnswer(BaseModel):
    query: str
    answer: str
    has_sufficient_evidence: bool
    evidence: List[EvidenceItem] = Field(default_factory=list)
    themes_detected: List[str] = Field(default_factory=list)
    markets_covered: List[str] = Field(default_factory=list)
