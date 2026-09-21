"""API routes for Cross-Transcript Q&A and Evidence deep-linking."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from apps.api.app.models.canonical import QueryAnswer, TranscriptSegment
from apps.api.app.agents.router import get_intent_router
from apps.api.app.services.analyzer import get_analyzer
from apps.api.app.services.repository import get_repository

router = APIRouter(prefix="/api", tags=["questions", "evidence"])


class AskQuestionRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Question across transcripts")
    market_filter: Optional[str] = Field(None, description="Optional market filter (France, Germany, UK)")


@router.post("/questions/ask", response_model=QueryAnswer)
async def ask_question(req: AskQuestionRequest):
    """Processes an arbitrary question across transcripts, grounded with exact quotes and timestamps."""
    router_agent = get_intent_router()
    return router_agent.process_query(req.query, market_filter=req.market_filter)


@router.post("/questions/ask-stream")
async def ask_question_stream(req: AskQuestionRequest):
    """Streams token-by-token answer via Server-Sent Events (SSE) followed by verified evidence chunk."""
    analyzer = get_analyzer()
    return StreamingResponse(
        analyzer.ask_question_stream(req.query, market_filter=req.market_filter),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/evidence/{segment_id}", response_model=TranscriptSegment)
async def get_evidence_segment(segment_id: str):
    """Deep-link lookup for an exact canonical transcript segment by segment_id."""
    repo = get_repository()
    seg = repo.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail=f"Evidence segment '{segment_id}' not found")
    return seg
