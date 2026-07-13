"""
PatternAgent — simple, explainable candlestick pattern detection
(bullish/bearish engulfing, doji, hammer) over the last few candles,
plus short-term trend-of-trend (momentum) via linear regression slope.
"""
import numpy as np
import pandas as pd


class PatternAgent:
    name = "PatternAgent"

    def analyze(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 5:
            return {"patterns": [], "momentum_score": 50.0, "note": "Insufficient candles."}

        patterns = []
        last2 = df.tail(2)
        o1, c1 = last2.iloc[0][["Open", "Close"]]
        o2, c2 = last2.iloc[1][["Open", "Close"]]

        # Bullish engulfing
        if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
            patterns.append("BULLISH_ENGULFING")
        # Bearish engulfing
        if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
            patterns.append("BEARISH_ENGULFING")

        last = df.iloc[-1]
        body = abs(last["Close"] - last["Open"])
        candle_range = max(last["High"] - last["Low"], 1e-9)
        if body / candle_range < 0.1:
            patterns.append("DOJI")

        lower_wick = min(last["Open"], last["Close"]) - last["Low"]
        if lower_wick > 2 * body and last["Close"] > last["Open"]:
            patterns.append("HAMMER")

        # Momentum: slope of a linear regression over the last 10 closes,
        # normalized into a 0-100 score.
        window = df.tail(10)["Close"].to_numpy()
        x = np.arange(len(window))
        slope = float(np.polyfit(x, window, 1)[0]) if len(window) >= 2 else 0.0
        norm_slope = slope / (window.mean() if window.mean() else 1)
        momentum_score = float(np.clip(50 + norm_slope * 5000, 0, 100))

        return {
            "patterns": patterns,
            "momentum_score": round(momentum_score, 2),
            "slope": round(slope, 6),
        }
