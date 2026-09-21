"""Tests for EvidenceValidator verifying exact quote matching and timestamp grounding."""

import pytest
from pathlib import Path
from apps.api.app.services.parser import parse_all_transcripts
from apps.api.app.services.validator import EvidenceValidator
from apps.api.app.models.canonical import EvidenceItem


@pytest.fixture
def validator():
    calls, experts = parse_all_transcripts(Path("data/transcripts"))
    return EvidenceValidator(calls=calls, experts=experts)


def test_validator_exact_quote(validator):
    # Dr. Jean Martin quote from Transcript_1_France.txt at 01:20
    candidate = {
        "call_id": "call_fr_01",
        "expert_id": "expert_fr_martin",
        "quote": "The biggest issue is still capital budget approval. Hospitals may like the technology clinically, but purchasing committees need a strong economic case before approving a system.",
    }
    res = validator.validate_quote(
        quote=candidate["quote"],
        call_id=candidate["call_id"],
        expert_id=candidate["expert_id"],
    )
    assert res.is_valid is True
    assert res.matched_segment is not None
    assert res.matched_segment.start_timestamp == "01:20"
    assert res.matched_segment.start_time_seconds == 80.0
    assert res.matched_segment.speaker == "Dr. Martin"


def test_validator_partial_sentence_match(validator):
    # Partial phrase from Anna Keller at 02:08
    phrase = "We look at total cost of ownership, expected procedure volume, maintenance, service contracts and training requirements."
    res = validator.validate_quote(
        quote=phrase,
        call_id="call_de_02",
    )
    assert res.is_valid is True
    assert res.matched_segment.start_timestamp == "02:08"
    assert res.matched_segment.speaker == "Anna Keller"


def test_validator_normalizes_quotes_and_whitespace(validator):
    # Emily Carter with leading/trailing spaces and slightly altered quotes
    phrase = '  "I think adoption could accelerate if training expands and systems become more cost competitive."  '
    res = validator.validate_quote(
        quote=phrase,
        expert_id="expert_gb_carter",
    )
    assert res.is_valid is True
    assert res.matched_segment.start_timestamp == "04:06"
    assert "adoption could accelerate" in res.verified_quote


def test_validator_rejects_hallucination(validator):
    fake_quote = "Robotic surgery is completely useless and no hospital will ever buy it in 2030."
    res = validator.validate_quote(
        quote=fake_quote,
        call_id="call_fr_01",
    )
    assert res.is_valid is False
    assert res.matched_segment is None
    assert "not found" in res.message.lower()


def test_validate_and_enrich_evidence_item(validator):
    raw_item = {
        "call_id": "call_fr_01",
        "expert_id": "expert_fr_martin",
        "speaker": "Dr. Martin",
        "quote": "Training matters, especially in the first year.",
        "relevance": "Surgeon training impact on hospital economics",
        # Notice: Deliberately omit or provide wrong timestamp to verify correction
        "start_timestamp": "99:99",
        "start_time_seconds": 999.0,
    }
    enriched = validator.enrich_evidence_item(raw_item)
    assert enriched is not None
    assert enriched.verified is True
    # Must have snapped to true canonical timestamp: 03:10 (190.0s)
    assert enriched.start_timestamp == "03:10"
    assert enriched.start_time_seconds == 190.0
    assert enriched.market == "France"
    assert enriched.expert_name == "Dr. Jean Martin"
