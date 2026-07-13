"""
HistoricalAgent — 5Y / 10Y (max available) daily price history.
Feeds the Technical, Pattern and Risk (volatility/drawdown) layers.
"""
import yfinance as yf
from app.agents.base_agent import BaseAgent


class HistoricalAgent(BaseAgent):
    name = "HistoricalAgent"

    def collect(self, ticker: str, period: str = "5y") -> dict:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=period, interval="1d")

        if hist.empty:
            # graceful degrade: shorter window for very new listings
            hist = tk.history(period="1y", interval="1d")

        if hist.empty:
            raise ValueError(f"No historical data available for '{ticker}'")

        hist = hist.reset_index()
        hist["Date"] = hist["Date"].astype(str)

        return {
            "period_used": period,
            "num_rows": len(hist),
            # Only return the columns downstream agents actually need,
            # to keep the orchestrator payload light.
            "records": hist[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict("records"),
        }
