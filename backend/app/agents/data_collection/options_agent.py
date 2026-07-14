"""
OptionsAgent — nearest-expiry option chain summary (put/call ratio,
implied-volatility skew) used as a sentiment/positioning signal.
Gracefully degrades for tickers with no listed options (e.g. many
non-US symbols).
"""
import yfinance as yf
from app.agents.base_agent import BaseAgent


class OptionsAgent(BaseAgent):
    name = "OptionsAgent"

    def collect(self, ticker: str) -> dict:
        tk = yf.Ticker(ticker)
        expiries = tk.options
        if not expiries:
            return {"available": False, "note": "No listed options for this ticker."}

        chain = tk.option_chain(expiries[0])
        calls, puts = chain.calls, chain.puts

        call_oi = int(calls["openInterest"].fillna(0).sum())
        put_oi = int(puts["openInterest"].fillna(0).sum())
        pcr = round(put_oi / call_oi, 3) if call_oi > 0 else None

        return {
            "available": True,
            "nearest_expiry": expiries[0],
            "call_open_interest": call_oi,
            "put_open_interest": put_oi,
            "put_call_ratio": pcr,
            "avg_call_iv": round(float(calls["impliedVolatility"].mean()), 4) if not calls.empty else None,
            "avg_put_iv": round(float(puts["impliedVolatility"].mean()), 4) if not puts.empty else None,
        }
