"""Tests for CanonicalRepository."""

import pytest
from apps.api.app.services.repository import CanonicalRepository


def test_repository_initialization(tmp_path):
    db_file = tmp_path / "test.db"
    repo = CanonicalRepository(db_path=str(db_file))

    calls = repo.get_all_calls()
    assert len(calls) == 3

    experts = repo.get_all_experts()
    assert len(experts) == 3

    france_call = repo.get_call("call_fr_01")
    assert france_call is not None
    assert france_call.market == "France"

    # Test segment lookup
    first_seg_id = france_call.segments[0].segment_id
    seg = repo.get_segment(first_seg_id)
    assert seg is not None
    assert seg.call_id == "call_fr_01"

    # Test keyword search
    matches = repo.search_segments(keywords=["budget", "capital", "roi"])
    assert len(matches) > 0
    assert any("capital" in s.text.lower() for s in matches)
