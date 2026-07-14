"""
Orchestrator Agent ("the brain").

Coordinates the full AlphaFlow AI pipeline for a single ticker:

  1. Data Collection layer  -> run all collector agents in parallel (asyncio.gather)
  2. Data Processing        -> normalize/validate raw data
  3. Analysis layer         -> Technical, Fundamental, Sentiment, Pattern, Event agents
  4. Feature Engineering    -> weighted composite score
  5. Prediction layer       -> expected return / profit probability / confidence
  6. Risk layer             -> volatility / liquidity / drawdown / event risk
  7. Recommendation layer   -> BUY / SELL / HOLD / WATCHLIST
  8. Explainability layer   -> human-readable reasoning

Returns an `AnalysisResponse` ready to be cached and served by the API.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.agents.data_collection.market_agent import MarketAgent
from app.agents.data_collection.historical_agent import HistoricalAgent
from app.agents.data_collection.news_agent import NewsAgent
from app.agents.data_collection.global_market_agent import GlobalMarketAgent
from app.agents.data_collection.fii_dii_agent import FiiDiiAgent
from app.agents.data_collection.options_agent import OptionsAgent
from app.agents.data_collection.company_agent import CompanyAgent

from app.agents.analysis.technical_agent import TechnicalAgent
from app.agents.analysis.fundamental_agent import FundamentalAgent
from app.agents.analysis.sentiment_agent import SentimentAgent
from app.agents.analysis.pattern_agent import PatternAgent
from app.agents.analysis.event_agent import EventAgent

from app.agents.prediction.prediction_agent import PredictionAgent
from app.agents.risk.risk_agent import RiskAgent
from app.agents.recommendation.recommendation_agent import RecommendationAgent
from app.agents.explainability.xai_agent import XAIAgent

from app.services.data_processing import historical_to_dataframe, data_quality_warnings
from app.services.feature_engineering import build_score_bundle, weighted_composite
from app.models.schemas import AnalysisResponse

logger = logging.getLogger("alphaflow.orchestrator")


class OrchestratorAgent:
    def __init__(self):
        # Data collection agents (run in parallel)
        self.collectors = {
            "market": MarketAgent(),
            "historical": HistoricalAgent(),
            "news": NewsAgent(),
            "global_market": GlobalMarketAgent(),
            "fii_dii": FiiDiiAgent(),
            "options": OptionsAgent(),
            "company": CompanyAgent(),
        }
        # Analysis agents (pure functions over normalized data)
        self.technical = TechnicalAgent()
        self.fundamental = FundamentalAgent()
        self.sentiment = SentimentAgent()
        self.pattern = PatternAgent()
        self.event = EventAgent()
        # Downstream layers
        self.prediction = PredictionAgent()
        self.risk = RiskAgent()
        self.recommendation = RecommendationAgent()
        self.xai = XAIAgent()

    async def run(self, ticker: str) -> AnalysisResponse:
        ticker = ticker.strip().upper()

        # 1. Data Collection layer — parallel fan-out
        tasks = {name: agent.run(ticker) for name, agent in self.collectors.items()}
        results = await asyncio.gather(*tasks.values())
        collected = dict(zip(tasks.keys(), results))

        warnings = data_quality_warnings(collected)

        # 2. Data Processing / Normalization
        hist_records = collected["historical"]["data"].get("records", [])
        df = historical_to_dataframe(hist_records)
        avg_volume = float(df["Volume"].tail(30).mean()) if not df.empty else None

        company_data = collected["company"]["data"]
        news_data = collected["news"]["data"]

        # 3. Analysis layer
        technical_result = self.technical.analyze(df)
        fundamental_result = self.fundamental.analyze(company_data)
        sentiment_result = self.sentiment.analyze(news_data.get("headlines", []))
        pattern_result = self.pattern.analyze(df)
        event_result = self.event.analyze(company_data.get("next_earnings_date"))

        # 4. Feature Engineering
        score_bundle = build_score_bundle(
            technical_score=technical_result["technical_score"],
            fundamental_score=fundamental_result["fundamental_score"],
            sentiment_score=sentiment_result["sentiment_score"],
            momentum_score=pattern_result["momentum_score"],
            event_score=event_result["event_score"],
        )
        composite = weighted_composite(score_bundle)

        # 5 & 6. Prediction + Risk (risk agent also derives recent volatility
        # which the prediction agent needs, so risk runs first)
        risk_result, recent_vol_pct = self.risk.assess(
            df, avg_volume, event_result["event_score"]
        )
        prediction_result = self.prediction.predict(composite, recent_vol_pct)

        # 7. Recommendation
        recommendation = self.recommendation.decide(score_bundle, prediction_result, risk_result)

        # 8. Explainability
        explanation = self.xai.explain(ticker, score_bundle, prediction_result,
                                        risk_result, recommendation)
        recommendation.explanation = explanation

        return AnalysisResponse(
            ticker=ticker,
            generated_at=datetime.now(timezone.utc).isoformat(),
            scores=score_bundle,
            prediction=prediction_result,
            risk=risk_result,
            recommendation=recommendation,
            warnings=warnings,
        )


_orchestrator_instance: OrchestratorAgent | None = None


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance
