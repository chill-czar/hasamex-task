"""API routes for interview calls and canonical transcripts."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from apps.api.app.models.canonical import Call, Expert, TranscriptSegment
from apps.api.app.services.repository import get_repository

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_interviews():
    """List all available expert calls with summary metadata."""
    repo = get_repository()
    calls = repo.get_all_calls()
    result = []
    for c in calls:
        expert = repo.get_expert(c.expert_id)
        result.append(
            {
                "call_id": c.call_id,
                "expert_id": c.expert_id,
                "expert_name": expert.name if expert else "Expert",
                "expert_role": expert.role if expert else "",
                "market": c.market,
                "country_code": expert.country_code if expert else "EU",
                "title": c.title,
                "total_duration_seconds": c.total_duration_seconds,
                "segment_count": len(c.segments),
                "source_file": c.source_file,
            }
        )
    return result


@router.get("/{call_id}", response_model=Call)
async def get_interview_detail(call_id: str):
    """Retrieve full canonical transcript and segments for a specific call."""
    repo = get_repository()
    call = repo.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail=f"Interview '{call_id}' not found")
    return call
