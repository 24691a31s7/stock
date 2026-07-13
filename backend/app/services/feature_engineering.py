"""
Feature Engineering layer.
Combines the raw per-agent scores into the ScoreBundle used by the
Prediction and Recommendation layers. Weights are centralized in
app.config so they can be tuned without redeploying agent code.
"""
from app.config import get_settings
from app.models.schemas import ScoreBundle

settings = get_settings()


def build_score_bundle(technical_score: float, fundamental_score: float,
                        sentiment_score: float, momentum_score: float,
                        event_score: float) -> ScoreBundle:
    return ScoreBundle(
        technical_score=technical_score,
        fundamental_score=fundamental_score,
        sentiment_score=sentiment_score,
        momentum_score=momentum_score,
        event_score=event_score,
    )


def weighted_composite(scores: ScoreBundle) -> float:
    """Single 0-100 composite score used as the backbone of the
    Prediction layer's profit-probability heuristic."""
    composite = (
        scores.technical_score * settings.technical_weight
        + scores.fundamental_score * settings.fundamental_weight
        + scores.sentiment_score * settings.sentiment_weight
        + scores.momentum_score * settings.momentum_weight
        + scores.event_score * settings.event_weight
    )
    return round(composite, 2)
