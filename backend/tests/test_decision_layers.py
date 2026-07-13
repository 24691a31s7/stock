from app.agents.risk.risk_agent import RiskAgent
from app.agents.prediction.prediction_agent import PredictionAgent
from app.agents.recommendation.recommendation_agent import RecommendationAgent
from app.services.feature_engineering import build_score_bundle, weighted_composite
from app.models.schemas import PredictionResult, RiskResult


def test_risk_agent_low_vol_scores_lower_than_high_vol(synthetic_ohlcv_df, flat_ohlcv_df):
    risk_flat, _ = RiskAgent().assess(flat_ohlcv_df, avg_daily_volume=1_000_000, event_score=80)
    risk_volatile, _ = RiskAgent().assess(synthetic_ohlcv_df, avg_daily_volume=1_000_000, event_score=80)
    assert risk_flat.overall_risk_score <= risk_volatile.overall_risk_score
    assert risk_flat.risk_label in {"Low", "Medium", "High"}


def test_risk_agent_handles_insufficient_data():
    import pandas as pd
    result, vol = RiskAgent().assess(pd.DataFrame(), None, 70)
    assert result.risk_label == "Medium"
    assert vol == 2.0


def test_prediction_agent_bullish_composite_gives_up_direction():
    result = PredictionAgent().predict(composite_score=85, recent_volatility_pct=2.0)
    assert result.price_direction == "UP"
    assert result.profit_probability > 50
    assert isinstance(result, PredictionResult)


def test_prediction_agent_bearish_composite_gives_down_direction():
    result = PredictionAgent().predict(composite_score=15, recent_volatility_pct=2.0)
    assert result.price_direction == "DOWN"
    assert result.profit_probability < 50


def test_feature_engineering_weighted_composite_in_range():
    bundle = build_score_bundle(70, 60, 55, 65, 80)
    composite = weighted_composite(bundle)
    assert 0 <= composite <= 100


def test_recommendation_agent_buy_case():
    bundle = build_score_bundle(70, 65, 65, 60, 80)
    prediction = PredictionResult(expected_return_pct=2.0, profit_probability=75,
                                   loss_probability=25, confidence_score=70, price_direction="UP")
    risk = RiskResult(volatility_score=20, liquidity_score=15, event_risk_score=20,
                       drawdown_score=15, overall_risk_score=20, risk_label="Low")
    rec = RecommendationAgent().decide(bundle, prediction, risk)
    assert rec.decision == "BUY"
    assert len(rec.reasons) > 0


def test_recommendation_agent_sell_case():
    bundle = build_score_bundle(30, 30, 30, 25, 30)
    prediction = PredictionResult(expected_return_pct=-3.0, profit_probability=20,
                                   loss_probability=80, confidence_score=60, price_direction="DOWN")
    risk = RiskResult(volatility_score=80, liquidity_score=70, event_risk_score=75,
                       drawdown_score=70, overall_risk_score=75, risk_label="High")
    rec = RecommendationAgent().decide(bundle, prediction, risk)
    assert rec.decision == "SELL"
