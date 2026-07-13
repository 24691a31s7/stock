"""
CompanyAgent — company fundamentals (PE, EPS, ROE, margins, debt).
Also surfaces the next earnings date, used by the EventAgent.
"""
import yfinance as yf
from app.agents.base_agent import BaseAgent


class CompanyAgent(BaseAgent):
    name = "CompanyAgent"

    def collect(self, ticker: str) -> dict:
        tk = yf.Ticker(ticker)
        info = tk.info or {}

        next_earnings = None
        try:
            cal = tk.calendar
            if isinstance(cal, dict) and cal.get("Earnings Date"):
                ed = cal["Earnings Date"]
                next_earnings = str(ed[0]) if isinstance(ed, list) else str(ed)
            elif hasattr(cal, "empty") and not cal.empty:
                next_earnings = str(cal.iloc[0, 0])
        except Exception:
            pass

        return {
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "roe": info.get("returnOnEquity"),
            "profit_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "next_earnings_date": next_earnings,
        }
