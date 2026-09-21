"""Tests for GroundedAnalyzer (Interview Guide, Themes, Disagreements, and Q&A)."""

import pytest
from apps.api.app.services.analyzer import GroundedAnalyzer


@pytest.fixture
def analyzer():
    return GroundedAnalyzer()


def test_interview_guide_analyses_complete(analyzer):
    analyses = analyzer.get_interview_guide_analyses()
    assert len(analyses) == 6

    for a in analyses:
        assert a.question_id in range(1, 7)
        assert len(a.question) > 10
        assert len(a.synthesized_answer) > 20
        # All 3 experts present in each question
        assert len(a.expert_answers) == 3
        for ea in a.expert_answers:
            assert ea.expert_id is not None
            assert len(ea.evidence) >= 1
            for ev in ea.evidence:
                assert ev.verified is True
                assert ev.quote != ""
                assert ev.start_timestamp != ""
                assert ev.start_time_seconds >= 0


def test_theme_analyses(analyzer):
    themes = analyzer.get_theme_analyses()
    assert len(themes) >= 4

    for theme in themes:
        assert len(theme.title) > 5
        assert len(theme.markets) >= 2
        assert len(theme.supporting_evidence) >= 2
        for ev in theme.supporting_evidence:
            assert ev.verified is True
            assert ev.start_timestamp != ""


def test_disagreement_analyses(analyzer):
    disagreements = analyzer.get_disagreement_analyses()
    assert len(disagreements) >= 3

    for item in disagreements:
        assert item.category is not None
        assert len(item.stances) >= 2
        for stance in item.stances:
            assert stance.evidence.verified is True
            assert stance.evidence.quote != ""


def test_ask_question_grounded(analyzer):
    res = analyzer.ask_question("What are the main barriers to robotic surgery adoption?")
    assert res.has_sufficient_evidence is True
    assert len(res.evidence) >= 1
    assert "barrier" in res.answer.lower() or "capital" in res.answer.lower()


def test_ask_question_insufficient_evidence(analyzer):
    res = analyzer.ask_question("What is the adoption of robotic surgery in Japan or China?")
    assert res.has_sufficient_evidence is False
    assert len(res.evidence) == 0
    assert any(term in res.answer.lower() for term in ["insufficient evidence", "do not contain", "no information", "not mentioned"])
