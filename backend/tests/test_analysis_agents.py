from app.agents.analysis.technical_agent import TechnicalAgent
from app.agents.analysis.fundamental_agent import FundamentalAgent
from app.agents.analysis.sentiment_agent import SentimentAgent
from app.agents.analysis.pattern_agent import PatternAgent
from app.agents.analysis.event_agent import EventAgent
import pandas as pd


def test_technical_agent_score_in_range(synthetic_ohlcv_df):
    result = TechnicalAgent().analyze(synthetic_ohlcv_df)
    assert 0 <= result["technical_score"] <= 100
    assert result["trend"] in {"BULLISH", "BEARISH", "NEUTRAL"}
    assert 0 <= result["rsi"] <= 100


def test_technical_agent_handles_empty_df():
    result = TechnicalAgent().analyze(pd.DataFrame())
    assert result["technical_score"] == 50.0


def test_technical_agent_handles_flat_series(flat_ohlcv_df):
    result = TechnicalAgent().analyze(flat_ohlcv_df)
    assert 0 <= result["technical_score"] <= 100


def test_fundamental_agent_rewards_strong_fundamentals():
    strong = {"pe_ratio": 15, "roe": 0.25, "profit_margin": 0.20, "debt_to_equity": 30, "eps": 5}
    weak = {"pe_ratio": 80, "roe": -0.05, "profit_margin": -0.02, "debt_to_equity": 200, "eps": -1}
    strong_score = FundamentalAgent().analyze(strong)["fundamental_score"]
    weak_score = FundamentalAgent().analyze(weak)["fundamental_score"]
    assert strong_score > weak_score


def test_fundamental_agent_handles_missing_data():
    result = FundamentalAgent().analyze({})
    assert result["fundamental_score"] == 50.0


def test_sentiment_agent_positive_vs_negative():
    positive = [{"title": "Company beats earnings, stock rallies on strong growth"}]
    negative = [{"title": "Company misses earnings amid fraud probe, shares plunge"}]
    pos_score = SentimentAgent().analyze(positive)["sentiment_score"]
    neg_score = SentimentAgent().analyze(negative)["sentiment_score"]
    assert pos_score > 50 > neg_score


def test_sentiment_agent_no_news_is_neutral():
    result = SentimentAgent().analyze([])
    assert result["sentiment_score"] == 50.0


def test_pattern_agent_returns_valid_structure(synthetic_ohlcv_df):
    result = PatternAgent().analyze(synthetic_ohlcv_df)
    assert "patterns" in result
    assert 0 <= result["momentum_score"] <= 100


def test_event_agent_imminent_earnings_lowers_score():
    from datetime import datetime, timedelta, timezone
    soon = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
    far = (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d")
    soon_score = EventAgent().analyze(soon)["event_score"]
    far_score = EventAgent().analyze(far)["event_score"]
    assert soon_score < far_score


def test_event_agent_handles_missing_date():
    result = EventAgent().analyze(None)
    assert result["event_score"] == 70.0
