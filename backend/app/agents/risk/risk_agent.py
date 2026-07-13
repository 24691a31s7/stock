"""
Risk Assessment Layer.
Computes Volatility, Liquidity, Event and Drawdown sub-scores from
historical price data, then aggregates them into an overall risk
score/label used by the Recommendation layer.

All sub-scores are on a 0-100 scale where HIGHER = RISKIER, except
where noted; the final aggregation inverts as needed.
"""
import numpy as np
import pandas as pd
from app.models.schemas import RiskResult


class RiskAgent:
    name = "RiskAgent"

    def assess(self, df: pd.DataFrame, avg_daily_volume: float | None,
               event_score: float) -> tuple[RiskResult, float]:
        """Returns (RiskResult, recent_volatility_pct) — the volatility
        figure is also reused by the Prediction layer."""
        if df.empty or len(df) < 10:
            recent_vol_pct = 2.0
            result = RiskResult(
                volatility_score=50.0, liquidity_score=50.0,
                event_risk_score=round(100 - event_score, 2),
                drawdown_score=50.0, overall_risk_score=55.0, risk_label="Medium",
            )
            return result, recent_vol_pct

        returns = df["Close"].pct_change().dropna()
        daily_vol = float(returns.std())
        annualized_vol_pct = daily_vol * np.sqrt(252) * 100
        recent_vol_pct = float(np.clip(returns.tail(20).std() * 100, 0.1, 20))

        # Volatility score: 0 (calm) -> 100 (extreme), soft-capped at 80% annualized
        volatility_score = float(np.clip((annualized_vol_pct / 80) * 100, 0, 100))

        # Liquidity: lower average volume => higher liquidity risk
        if avg_daily_volume is None or avg_daily_volume <= 0:
            liquidity_score = 60.0
        elif avg_daily_volume > 5_000_000:
            liquidity_score = 10.0
        elif avg_daily_volume > 1_000_000:
            liquidity_score = 25.0
        elif avg_daily_volume > 100_000:
            liquidity_score = 50.0
        else:
            liquidity_score = 85.0

        # Drawdown: max peak-to-trough decline over the observed window
        cum_max = df["Close"].cummax()
        drawdown = (df["Close"] - cum_max) / cum_max
        max_drawdown_pct = float(abs(drawdown.min()) * 100)
        drawdown_score = float(np.clip((max_drawdown_pct / 50) * 100, 0, 100))

        event_risk_score = float(np.clip(100 - event_score, 0, 100))

        overall = (
            volatility_score * 0.35
            + liquidity_score * 0.20
            + drawdown_score * 0.25
            + event_risk_score * 0.20
        )
        overall = float(np.clip(overall, 0, 100))

        if overall < 35:
            label = "Low"
        elif overall < 65:
            label = "Medium"
        else:
            label = "High"

        result = RiskResult(
            volatility_score=round(volatility_score, 2),
            liquidity_score=round(liquidity_score, 2),
            event_risk_score=round(event_risk_score, 2),
            drawdown_score=round(drawdown_score, 2),
            overall_risk_score=round(overall, 2),
            risk_label=label,
        )
        return result, recent_vol_pct
