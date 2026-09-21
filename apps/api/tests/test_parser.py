"""Tests for transcript parsing and canonical model generation."""

import pytest
from pathlib import Path
from apps.api.app.services.parser import (
    parse_timestamp_to_seconds,
    seconds_to_timestamp,
    parse_transcript_file,
    parse_all_transcripts,
)


def test_timestamp_conversions():
    assert parse_timestamp_to_seconds("00:00") == 0.0
    assert parse_timestamp_to_seconds("00:18") == 18.0
    assert parse_timestamp_to_seconds("01:12") == 72.0
    assert parse_timestamp_to_seconds("06:08") == 368.0

    assert seconds_to_timestamp(0.0) == "00:00"
    assert seconds_to_timestamp(18.0) == "00:18"
    assert seconds_to_timestamp(72.0) == "01:12"
    assert seconds_to_timestamp(368.0) == "06:08"


def test_parse_france_transcript(tmp_path):
    france_content = """Expert 1 – Dr. Jean Martin
Role: Head of Urology
Market: France

00:00
Interviewer: Thanks for joining. To begin, how would you describe robotic surgery adoption in France today?

00:18
Dr. Martin: Adoption is growing, but it is still concentrated in larger academic hospitals and private centres with stronger capital budgets. Smaller regional hospitals are much slower.
"""
    f = tmp_path / "Transcript_1_France.txt"
    f.write_text(france_content)

    call, expert = parse_transcript_file(f, call_id="call_fr_01")

    assert expert.expert_id == "expert_fr_martin"
    assert expert.name == "Dr. Jean Martin"
    assert expert.role == "Head of Urology"
    assert expert.market == "France"

    assert call.call_id == "call_fr_01"
    assert call.market == "France"
    assert len(call.segments) == 2

    seg1 = call.segments[0]
    assert seg1.speaker == "Interviewer"
    assert seg1.is_expert is False
    assert seg1.start_timestamp == "00:00"
    assert seg1.start_time_seconds == 0.0
    assert seg1.end_timestamp == "00:18"
    assert seg1.end_time_seconds == 18.0

    seg2 = call.segments[1]
    assert seg2.speaker == "Dr. Martin"
    assert seg2.is_expert is True
    assert seg2.start_timestamp == "00:18"
    assert seg2.start_time_seconds == 18.0
    assert "Adoption is growing" in seg2.text


def test_parse_all_real_transcripts():
    base_dir = Path("data/transcripts")
    calls, experts = parse_all_transcripts(base_dir)

    assert len(calls) == 3
    assert len(experts) == 3

    markets = {call.market for call in calls}
    assert markets == {"France", "Germany", "United Kingdom"}

    expert_names = {exp.name for exp in experts}
    assert "Dr. Jean Martin" in expert_names
    assert "Anna Keller" in expert_names
    assert "Dr. Emily Carter" in expert_names

    # Check total segments across all 3 transcripts
    total_segments = sum(len(c.segments) for c in calls)
    assert total_segments > 20
    for call in calls:
        for seg in call.segments:
            assert seg.text != ""
            assert seg.start_time_seconds <= seg.end_time_seconds
            assert seg.segment_id.startswith(call.call_id)
