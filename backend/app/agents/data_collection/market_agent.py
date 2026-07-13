"""
MarketAgent — live / intraday price data.
Data source: yfinance (free, keyless). Falls back gracefully to the
latest daily candle if intraday data is unavailable (e.g. market closed
or a low-liquidity ticker).
"""
import yfinance as yf
from app.agents.base_agent import BaseAgent


class MarketAgent(BaseAgent):
    name = "MarketAgent"

    def collect(self, ticker: str) -> dict:
        tk = yf.Ticker(ticker)

        intraday = tk.history(period="1d", interval="5m")
        if intraday.empty:
            intraday = tk.history(period="5d", interval="1d")

        if intraday.empty:
            raise ValueError(f"No live market data available for '{ticker}'")

        last = intraday.iloc[-1]
        prev_close = tk.fast_info.get("previous_close") if hasattr(tk, "fast_info") else None
        if prev_close is None:
            prev_close = intraday.iloc[0]["Open"]

        change_pct = ((last["Close"] - prev_close) / prev_close) * 100 if prev_close else 0.0

        return {
            "last_price": round(float(last["Close"]), 4),
            "day_open": round(float(intraday.iloc[0]["Open"]), 4),
            "day_high": round(float(intraday["High"].max()), 4),
            "day_low": round(float(intraday["Low"].min()), 4),
            "volume": int(intraday["Volume"].sum()),
            "change_pct": round(float(change_pct), 4),
            "as_of": str(last.name),
        }
