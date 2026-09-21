"""API routes for Cross-Call Themes and Disagreements."""

from fastapi import APIRouter
from typing import List
from apps.api.app.models.canonical import ThemeItem, DisagreementItem
from apps.api.app.services.analyzer import get_analyzer

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/themes", response_model=List[ThemeItem])
async def get_themes():
    """Retrieve common themes identified across France, Germany, and the UK."""
    analyzer = get_analyzer()
    return analyzer.get_theme_analyses()


@router.get("/disagreements", response_model=List[DisagreementItem])
async def get_disagreements():
    """Retrieve contrasting viewpoints and disagreements classified along the nuance spectrum."""
    analyzer = get_analyzer()
    return analyzer.get_disagreement_analyses()
