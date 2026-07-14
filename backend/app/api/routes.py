"""
Presentation-facing REST API. Thin layer: validates input, delegates
to the Orchestrator, caches results, and persists a lightweight audit
trail to the Storage layer.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import get_orchestrator
from app.cache.redis_cache import get_cache
from app.db.database import get_db, AnalysisRecord
from app.models.schemas import AnalysisResponse

logger = logging.getLogger("alphaflow.api")
router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/analyze/{ticker}", response_model=AnalysisResponse)
async def analyze_ticker(ticker: str, db: Session = Depends(get_db)):
    ticker = ticker.strip().upper()
    if not ticker or len(ticker) > 15:
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")

    cache = get_cache()
    cache_key = f"analysis:{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return AnalysisResponse(**cached)

    orchestrator = get_orchestrator()
    try:
        result = await orchestrator.run(ticker)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Orchestrator failed for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc

    cache.set(cache_key, result.model_dump())

    try:
        db.add(AnalysisRecord(
            ticker=result.ticker,
            decision=result.recommendation.decision,
            expected_return_pct=result.prediction.expected_return_pct,
            profit_probability=result.prediction.profit_probability,
            risk_label=result.risk.risk_label,
            confidence_score=result.prediction.confidence_score,
            explanation=result.recommendation.explanation,
        ))
        db.commit()
    except Exception:
        logger.warning("Could not persist analysis history for %s", ticker)
        db.rollback()

    return result


@router.get("/history/{ticker}")
async def get_history(ticker: str, limit: int = 20, db: Session = Depends(get_db)):
    ticker = ticker.strip().upper()
    records = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.ticker == ticker)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "ticker": r.ticker,
            "decision": r.decision,
            "expected_return_pct": r.expected_return_pct,
            "profit_probability": r.profit_probability,
            "risk_label": r.risk_label,
            "confidence_score": r.confidence_score,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
