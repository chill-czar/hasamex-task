"""End-to-End API Integration Tests for Hasamex Interview Analysis Platform."""

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app


@pytest.mark.asyncio
async def test_api_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["canonical_calls_loaded"] == 3
        assert data["canonical_experts_loaded"] == 3


@pytest.mark.asyncio
async def test_api_list_and_get_interview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/interviews")
        assert res.status_code == 200
        calls = res.json()
        assert len(calls) == 3

        call_id = calls[0]["call_id"]
        res_detail = await ac.get(f"/api/interviews/{call_id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["call_id"] == call_id
        assert len(detail["segments"]) > 0


@pytest.mark.asyncio
async def test_api_interview_guide():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/interview-guide")
        assert res.status_code == 200
        questions = res.json()
        assert len(questions) == 6

        q1 = questions[0]
        assert q1["question_id"] == 1
        assert len(q1["expert_answers"]) == 3
        for ea in q1["expert_answers"]:
            assert len(ea["evidence"]) >= 1
            for ev in ea["evidence"]:
                assert ev["verified"] is True
                assert ev["quote"] != ""
                assert ev["start_timestamp"] != ""

        # Test single question endpoint
        res_single = await ac.get("/api/interview-guide/2")
        assert res_single.status_code == 200
        assert res_single.json()["question_id"] == 2


@pytest.mark.asyncio
async def test_api_insights_themes_and_disagreements():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_themes = await ac.get("/api/insights/themes")
        assert res_themes.status_code == 200
        themes = res_themes.json()
        assert len(themes) >= 4

        res_disagree = await ac.get("/api/insights/disagreements")
        assert res_disagree.status_code == 200
        disagreements = res_disagree.json()
        assert len(disagreements) >= 3


@pytest.mark.asyncio
async def test_api_ask_questions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Grounded question
        payload = {"query": "What are the main adoption barriers across Europe?"}
        res = await ac.post("/api/questions/ask", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["has_sufficient_evidence"] is True
        assert len(data["evidence"]) > 0

        # Deep link test to evidence segment
        seg_id = data["evidence"][0]["segment_id"]
        res_ev = await ac.get(f"/api/evidence/{seg_id}")
        assert res_ev.status_code == 200
        seg_data = res_ev.json()
        assert seg_data["segment_id"] == seg_id
        assert seg_data["text"] != ""

        # Insufficient evidence question
        payload_invalid = {"query": "What is the pediatric robotic surgery market in Japan?"}
        res_invalid = await ac.post("/api/questions/ask", json=payload_invalid)
        assert res_invalid.status_code == 200
        data_invalid = res_invalid.json()
        assert data_invalid["has_sufficient_evidence"] is False
        assert len(data_invalid["evidence"]) == 0


@pytest.mark.asyncio
async def test_api_ask_questions_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"query": "What are the main adoption barriers?"}
        res = await ac.post("/api/questions/ask-stream", json=payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body = res.text
        assert "event: token" in body or "event: evidence" in body
        assert "event: done" in body
