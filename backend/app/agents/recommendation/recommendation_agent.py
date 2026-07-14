"""
Recommendation Intelligence layer.
Combines scores, prediction and risk into a final BUY / SELL / HOLD /
WATCHLIST decision using transparent, documented thresholds.
"""
from app.models.schemas import ScoreBundle, PredictionResult, RiskResult, Recommendation


class RecommendationAgent:
    name = "RecommendationAgent"

    def decide(self, scores: ScoreBundle, prediction: PredictionResult,
               risk: RiskResult) -> Recommendation:
        reasons: list[str] = []

        buy_signal = (
            prediction.profit_probability >= 65
            and prediction.expected_return_pct > 0.5
            and risk.overall_risk_score < 65
            and prediction.confidence_score >= 55
        )
        sell_signal = (
            prediction.profit_probability <= 35
            or prediction.expected_return_pct < -1.0
            or (risk.overall_risk_score >= 80 and prediction.price_direction == "DOWN")
        )
        watchlist_signal = (
            not buy_signal and not sell_signal
            and (45 <= prediction.profit_probability <= 65)
            and prediction.confidence_score < 55
        )

        if buy_signal:
            decision = "BUY"
        elif sell_signal:
            decision = "SELL"
        elif watchlist_signal:
            decision = "WATCHLIST"
        else:
            decision = "HOLD"

        # Reasoning inputs (kept as short, evidence-style bullets — the
        # XAI agent turns these into full prose).
        if scores.sentiment_score >= 60:
            reasons.append("Positive news sentiment")
        elif scores.sentiment_score <= 40:
            reasons.append("Negative news sentiment")

        if scores.technical_score >= 60:
            reasons.append("Strong technical trend")
        elif scores.technical_score <= 40:
            reasons.append("Weak technical trend")

        if scores.fundamental_score >= 60:
            reasons.append("Healthy fundamentals")
        elif scores.fundamental_score <= 40:
            reasons.append("Weak fundamentals")

        if risk.risk_label == "Low":
            reasons.append("Low overall risk profile")
        elif risk.risk_label == "High":
            reasons.append("Elevated risk profile")

        reasons.append(f"Profit probability {prediction.profit_probability}%")
        reasons.append(f"Expected return {prediction.expected_return_pct:+.2f}%")

        return Recommendation(decision=decision, reasons=reasons, explanation="")
