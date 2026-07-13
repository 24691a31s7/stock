"""
Explainable AI (XAI) Agent.
Turns the structured Recommendation + scores/prediction/risk into a
human-readable explanation string — the "Why Buy? / Why Sell?" layer.
"""
from app.models.schemas import ScoreBundle, PredictionResult, RiskResult, Recommendation


class XAIAgent:
    name = "XAIAgent"

    def explain(self, ticker: str, scores: ScoreBundle, prediction: PredictionResult,
                risk: RiskResult, recommendation: Recommendation) -> str:
        bullets = "\n".join(f" • {r}" for r in recommendation.reasons)
        return (
            f"Recommended {recommendation.decision} for {ticker} because:\n"
            f"{bullets}\n"
            f" • Risk level: {risk.risk_label} (score {risk.overall_risk_score}/100)\n"
            f" • Confidence: {prediction.confidence_score}%\n"
            f" • Direction bias: {prediction.price_direction}"
        )
