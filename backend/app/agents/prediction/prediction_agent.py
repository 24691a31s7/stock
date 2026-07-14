"""
Prediction Layer.

IMPORTANT (transparency note): this is a documented, rule-based
statistical heuristic — not a trained ML model. It converts the
composite feature score + recent realized volatility into:
  - expected_return_pct
  - profit_probability / loss_probability
  - confidence_score
  - price_direction

This module is intentionally isolated behind `PredictionAgent.predict()`
so it can be swapped for a trained model (e.g. gradient boosting /
LSTM) without touching any other layer — feed it the same
`composite_score` + `recent_volatility` inputs and return the same
`PredictionResult` shape.
"""
import numpy as np
from app.models.schemas import PredictionResult


class PredictionAgent:
    name = "PredictionAgent"

    def predict(self, composite_score: float, recent_volatility_pct: float) -> PredictionResult:
        # Map composite score (0-100, centered at 50) to a probability
        # of positive return using a logistic-style squashing function.
        centered = (composite_score - 50) / 50  # -1..1
        profit_probability = 1 / (1 + np.exp(-3 * centered))  # sigmoid
        profit_probability = float(np.clip(profit_probability * 100, 1, 99))
        loss_probability = round(100 - profit_probability, 2)

        # Expected return scales with conviction (distance from neutral)
        # and is capped relative to recent volatility, so highly volatile
        # names don't produce unrealistically large point estimates.
        conviction = abs(centered)
        expected_return = conviction * min(recent_volatility_pct, 8) * (1 if centered >= 0 else -1)

        # Confidence reflects both conviction and data completeness
        # (volatility as a rough proxy for signal noise).
        noise_penalty = min(recent_volatility_pct / 10, 0.4)
        confidence = float(np.clip((conviction * 100) - (noise_penalty * 100) + 50, 5, 98))

        if centered > 0.05:
            direction = "UP"
        elif centered < -0.05:
            direction = "DOWN"
        else:
            direction = "FLAT"

        return PredictionResult(
            expected_return_pct=round(expected_return, 2),
            profit_probability=round(profit_probability, 2),
            loss_probability=loss_probability,
            confidence_score=round(confidence, 2),
            price_direction=direction,
        )
