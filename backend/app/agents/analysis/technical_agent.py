"""
TechnicalAgent — computes RSI(14), MACD(12,26,9) and EMA(20/50/200)
from historical closing prices and derives a 0-100 technical_score.

All indicators are computed manually with pandas/numpy (no TA-lib
dependency) so the container stays lightweight.
"""
import numpy as np
import pandas as pd


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0


def _macd(close: pd.Series, fast=12, slow=26, signal=9) -> dict:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def _ema(close: pd.Series, span: int) -> float:
    return float(close.ewm(span=span, adjust=False).mean().iloc[-1])


class TechnicalAgent:
    name = "TechnicalAgent"

    def analyze(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 30:
            return {
                "rsi": 50.0, "macd": {"macd": 0, "signal": 0, "histogram": 0},
                "ema_20": None, "ema_50": None, "ema_200": None,
                "technical_score": 50.0, "trend": "NEUTRAL",
                "note": "Insufficient history for reliable technical analysis.",
            }

        close = df["Close"]
        rsi = _rsi(close)
        macd = _macd(close)
        ema20 = _ema(close, 20)
        ema50 = _ema(close, 50)
        ema200 = _ema(close, 200) if len(close) >= 200 else _ema(close, len(close))
        last_price = float(close.iloc[-1])

        # --- Scoring heuristic (0-100), documented and easy to tune ---
        score = 50.0
        # RSI: reward pulling out of oversold, penalize overbought
        if rsi < 30:
            score += 15
        elif rsi > 70:
            score -= 15
        else:
            score += (rsi - 50) * 0.2

        # MACD histogram momentum
        score += 15 if macd["histogram"] > 0 else -15

        # Price vs EMA trend stack (golden/death cross style logic)
        if last_price > ema20 > ema50:
            score += 15
            trend = "BULLISH"
        elif last_price < ema20 < ema50:
            score -= 15
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        score = float(np.clip(score, 0, 100))

        return {
            "rsi": round(rsi, 2),
            "macd": {k: round(v, 4) for k, v in macd.items()},
            "ema_20": round(ema20, 4),
            "ema_50": round(ema50, 4),
            "ema_200": round(ema200, 4),
            "last_price": round(last_price, 4),
            "trend": trend,
            "technical_score": round(score, 2),
        }
