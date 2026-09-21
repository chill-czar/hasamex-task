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


def test_materialized_analysis_persistence(tmp_path):
    db_file = tmp_path / "test_mat.db"
    repo = CanonicalRepository(db_path=str(db_file))

    # Save an analysis
    repo.save_materialized_analysis(
        key="guide_q1",
        content_hash="abc123hash",
        payload_json='{"question_id": 1, "answer": "Test Answer"}',
    )

    # Retrieve single
    res = repo.get_materialized_analysis("guide_q1")
    assert res is not None
    assert res["content_hash"] == "abc123hash"
    assert "Test Answer" in res["payload_json"]

    # Non-existent
    assert repo.get_materialized_analysis("guide_q999") is None

    # Retrieve all
    all_res = repo.get_all_materialized_analyses()
    assert "guide_q1" in all_res
    assert all_res["guide_q1"]["content_hash"] == "abc123hash"

    # Test update (upsert)
    repo.save_materialized_analysis(
        key="guide_q1",
        content_hash="def456updated",
        payload_json='{"question_id": 1, "answer": "Updated Answer"}',
    )
    res_updated = repo.get_materialized_analysis("guide_q1")
    assert res_updated["content_hash"] == "def456updated"
    assert "Updated Answer" in res_updated["payload_json"]
