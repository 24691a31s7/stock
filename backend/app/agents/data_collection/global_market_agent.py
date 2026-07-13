"""
GlobalMarketAgent — snapshot of major world indices (US / EU / Asia)
used as a macro backdrop signal for the Momentum score.
"""
import yfinance as yf
from app.agents.base_agent import BaseAgent

INDICES = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "FTSE100": "^FTSE",
    "DAX": "^GDAXI",
    "NIKKEI225": "^N225",
    "HANGSENG": "^HSI",
    "NIFTY50": "^NSEI",
}


class GlobalMarketAgent(BaseAgent):
    name = "GlobalMarketAgent"

    def collect(self, ticker: str) -> dict:
        # ticker arg unused here on purpose — this is a macro/global snapshot,
        # but kept in the signature to satisfy the common agent contract.
        snapshot = {}
        data = yf.download(list(INDICES.values()), period="5d", interval="1d",
                            group_by="ticker", progress=False, threads=True)

        for name, symbol in INDICES.items():
            try:
                closes = data[symbol]["Close"].dropna()
                if len(closes) >= 2:
                    chg = ((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2]) * 100
                    snapshot[name] = round(float(chg), 3)
            except Exception:
                continue

        global_bias = "RISK_ON" if sum(snapshot.values()) > 0 else "RISK_OFF"
        return {"indices_change_pct": snapshot, "global_bias": global_bias}
