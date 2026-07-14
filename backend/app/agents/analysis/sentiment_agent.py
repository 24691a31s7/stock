"""
SentimentAgent — lightweight lexicon-based sentiment scoring over
recent news headlines. Intentionally dependency-free (no external NLP
API) so the system runs fully offline/keyless; swap in a transformer
model or hosted NLP API here for production-grade sentiment.
"""
import re
import numpy as np

POSITIVE_WORDS = {
    "beat", "beats", "surge", "surges", "rally", "rallies", "growth", "profit",
    "record", "upgrade", "upgraded", "strong", "gain", "gains", "bullish",
    "outperform", "buyback", "expansion", "soar", "soars", "positive", "rise", "rises",
    "jump", "jumps", "boost", "top", "tops", "win", "wins", "approval", "approved",
}
NEGATIVE_WORDS = {
    "miss", "misses", "plunge", "plunges", "fall", "falls", "loss", "losses",
    "downgrade", "downgraded", "weak", "decline", "declines", "bearish",
    "underperform", "lawsuit", "fraud", "scandal", "recall", "layoff", "layoffs",
    "crash", "crashes", "drop", "drops", "cut", "cuts", "probe", "investigation",
    "bankruptcy", "default", "delay", "delayed",
}


def _score_headline(title: str) -> int:
    words = set(re.findall(r"[a-zA-Z']+", title.lower()))
    return len(words & POSITIVE_WORDS) - len(words & NEGATIVE_WORDS)


class SentimentAgent:
    name = "SentimentAgent"

    def analyze(self, headlines: list[dict]) -> dict:
        if not headlines:
            return {"sentiment_score": 50.0, "positive_count": 0, "negative_count": 0,
                     "note": "No recent news found; defaulting to neutral."}

        raw_scores = [_score_headline(h["title"]) for h in headlines]
        positive = sum(1 for s in raw_scores if s > 0)
        negative = sum(1 for s in raw_scores if s < 0)
        net = sum(raw_scores)

        # Map net lexicon score to a 0-100 scale, centered at 50.
        score = 50 + (net / max(len(headlines), 1)) * 25
        score = float(np.clip(score, 0, 100))

        return {
            "sentiment_score": round(score, 2),
            "positive_count": positive,
            "negative_count": negative,
            "headlines_analyzed": len(headlines),
        }
