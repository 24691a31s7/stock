"""
Pydantic schemas shared across agents, services and API routes.
Keeping these centralized keeps every layer's contract in sync.
"""
from typing import Optional
from pydantic import BaseModel, Field


class TickerRequest(BaseModel):
    ticker: str = Field(..., examples=["AAPL", "SBIN.NS", "RELIANCE.NS"])


class ScoreBundle(BaseModel):
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    momentum_score: float
    event_score: float


class PredictionResult(BaseModel):
    expected_return_pct: float
    profit_probability: float
    loss_probability: float
    confidence_score: float
    price_direction: str  # "UP" | "DOWN" | "FLAT"


class RiskResult(BaseModel):
    volatility_score: float
    liquidity_score: float
    event_risk_score: float
    drawdown_score: float
    overall_risk_score: float
    risk_label: str  # "Low" | "Medium" | "High"


class Recommendation(BaseModel):
    decision: str  # "BUY" | "SELL" | "HOLD" | "WATCHLIST"
    reasons: list[str]
    explanation: str


class AnalysisResponse(BaseModel):
    ticker: str
    generated_at: str
    scores: ScoreBundle
    prediction: PredictionResult
    risk: RiskResult
    recommendation: Recommendation
    warnings: list[str] = []
