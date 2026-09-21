"""API routes for Interview Guide analyses."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from apps.api.app.models.canonical import GuideQuestionAnalysis
from apps.api.app.services.analyzer import get_analyzer

router = APIRouter(prefix="/api/interview-guide", tags=["interview-guide"])


class AnalyzeRequest(BaseModel):
    question_id: int
    force_refresh: bool = False


@router.get("", response_model=List[GuideQuestionAnalysis])
async def get_all_guide_questions():
    """Retrieve all 6 interview guide questions with synthesized answers and expert quotes."""
    analyzer = get_analyzer()
    return analyzer.get_interview_guide_analyses()


@router.get("/{question_id}", response_model=GuideQuestionAnalysis)
async def get_single_guide_question(question_id: int):
    """Retrieve analysis for a specific guide question (1 to 6)."""
    analyzer = get_analyzer()
    analysis = analyzer.get_guide_question_analysis(question_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Guide question {question_id} not found")
    return analysis


@router.post("/analyze", response_model=GuideQuestionAnalysis)
async def analyze_guide_question(req: AnalyzeRequest):
    """Trigger analysis of a specific guide question."""
    analyzer = get_analyzer()
    analysis = analyzer.get_guide_question_analysis(req.question_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Guide question {req.question_id} not found")
    return analysis
